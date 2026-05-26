#include "inference.h"
#include "features.h"
#include "esp_log.h"
#include <string.h>
#include <math.h>

/*
 * TFLite Micro C API wrappers.
 * The actual model C arrays (model_anomaly.h, model_occupancy.h) are generated
 * by the ml/ training pipeline and placed here before building.
 * They are conditionally included so the firmware compiles without them during
 * early development — inference functions return 0.0 as a safe default.
 */
#if __has_include("model_anomaly.h") && __has_include("model_occupancy.h")
#  include "model_anomaly.h"
#  include "model_occupancy.h"
#  include "tensorflow/lite/micro/micro_interpreter.h"
#  include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#  include "tensorflow/lite/schema/schema_generated.h"
#  define MODELS_AVAILABLE 1
#else
#  define MODELS_AVAILABLE 0
#endif

static const char *TAG = "INFERENCE";

#if MODELS_AVAILABLE
static uint8_t s_arena[TFLITE_ARENA_SIZE];
static tflite::MicroInterpreter *s_anomaly_interp   = NULL;
static tflite::MicroInterpreter *s_occupancy_interp = NULL;
#endif

void inference_init(void)
{
#if MODELS_AVAILABLE
    static tflite::MicroMutableOpResolver<6> resolver;
    resolver.AddFullyConnected();
    resolver.AddLstm();
    resolver.AddQuantize();
    resolver.AddDequantize();
    resolver.AddReshape();
    resolver.AddLogistic();

    const tflite::Model *anomaly_model =
        tflite::GetModel(g_model_anomaly);
    static tflite::MicroInterpreter anomaly_interp(
        anomaly_model, resolver, s_arena, TFLITE_ARENA_SIZE / 2);
    anomaly_interp.AllocateTensors();
    s_anomaly_interp = &anomaly_interp;

    const tflite::Model *occupancy_model =
        tflite::GetModel(g_model_occupancy);
    static tflite::MicroInterpreter occupancy_interp(
        occupancy_model, resolver,
        s_arena + TFLITE_ARENA_SIZE / 2, TFLITE_ARENA_SIZE / 2);
    occupancy_interp.AllocateTensors();
    s_occupancy_interp = &occupancy_interp;

    ESP_LOGI(TAG, "TFLite Micro models loaded");
#else
    ESP_LOGW(TAG, "No model headers found — inference returns defaults");
#endif
}

float inference_run_anomaly(const float *power_window, size_t len)
{
#if MODELS_AVAILABLE
    if (!s_anomaly_interp) return 0.0f;

    TfLiteTensor *input = s_anomaly_interp->input(0);
    features_normalize_window(power_window, len,
                               (int8_t *)input->data.int8,
                               input->params.scale,
                               input->params.zero_point);

    s_anomaly_interp->Invoke();

    TfLiteTensor *output = s_anomaly_interp->output(0);
    /* Reconstruction error as mean squared difference from input */
    float mse = 0.0f;
    for (size_t i = 0; i < len; i++) {
        float orig  = power_window[i];
        float recon = (output->data.int8[i] - output->params.zero_point)
                      * output->params.scale;
        float diff  = orig - recon;
        mse += diff * diff;
    }
    return mse / (float)len;
#else
    return 0.0f;
#endif
}

float inference_run_occupancy(float power_w, bool motion, float temperature)
{
#if MODELS_AVAILABLE
    if (!s_occupancy_interp) return 0.0f;

    TfLiteTensor *input = s_occupancy_interp->input(0);
    float raw_features[3] = { power_w, motion ? 1.0f : 0.0f, temperature };
    features_quantize(raw_features, 3,
                      (int8_t *)input->data.int8,
                      input->params.scale,
                      input->params.zero_point);

    s_occupancy_interp->Invoke();

    TfLiteTensor *output = s_occupancy_interp->output(0);
    float prob = (output->data.int8[0] - output->params.zero_point)
                 * output->params.scale;
    /* Clamp to [0, 1] */
    return prob < 0.0f ? 0.0f : (prob > 1.0f ? 1.0f : prob);
#else
    return 0.0f;
#endif
}
