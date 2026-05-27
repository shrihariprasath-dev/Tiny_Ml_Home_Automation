import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  late final Dio _dio;

  static const _baseUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000',
  );

  ApiClient(FlutterSecureStorage storage) {
    _dio = Dio(BaseOptions(
      baseUrl:        _baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers:        {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) {
        handler.next(error);
      },
    ));
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await _dio.post<Map<String, dynamic>>('/auth/login', data: {
      'email':    email,
      'password': password,
    });
    return res.data!;
  }

  Future<List<dynamic>> getDevices() async {
    final res = await _dio.get<List<dynamic>>('/api/devices');
    return res.data!;
  }

  Future<void> controlRelay(String deviceId, int relay, bool state) async {
    await _dio.put('/api/devices/$deviceId/relay', data: {
      'relay': relay,
      'state': state,
    });
  }

  Future<Map<String, dynamic>> getRealtimeEnergy() async {
    final res = await _dio.get<Map<String, dynamic>>('/api/energy/realtime');
    return res.data!;
  }

  Future<List<dynamic>> getAlerts({bool acknowledgedOnly = false}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/alerts',
      queryParameters: acknowledgedOnly ? null : {'acknowledged': 'false'},
    );
    return res.data!;
  }

  Future<void> acknowledgeAlert(String alertId) async {
    await _dio.put('/api/alerts/$alertId/acknowledge');
  }

  Future<Map<String, dynamic>> getForecast(String deviceId) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '/api/ai/forecast',
      queryParameters: {'device_id': deviceId},
    );
    return res.data!;
  }
}
