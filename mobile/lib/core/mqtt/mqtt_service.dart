import 'dart:async';
import 'dart:convert';
import 'package:mqtt_client/mqtt_client.dart';
import 'package:mqtt_client/mqtt_server_client.dart';

typedef TelemetryCallback = void Function(Map<String, dynamic> payload);

class MqttService {
  late final MqttServerClient _client;
  final _telemetryController = StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get telemetryStream => _telemetryController.stream;

  static const _broker    = String.fromEnvironment('MQTT_HOST',     defaultValue: 'localhost');
  static const _port      = int.fromEnvironment('MQTT_PORT',        defaultValue: 1883);
  static const _clientId  = 'flutter_dashboard';

  Future<void> connect(String deviceId, String secret) async {
    _client = MqttServerClient.withPort(_broker, _clientId, _port);
    _client.logging(on: false);
    _client.keepAlivePeriod = 30;
    _client.autoReconnect   = true;
    _client.resubscribeOnAutoReconnect = true;

    _client.onDisconnected    = _onDisconnected;
    _client.onConnected       = _onConnected;
    _client.onAutoReconnected = _onAutoReconnected;

    final connMessage = MqttConnectMessage()
        .withClientIdentifier(_clientId)
        .authenticateAs(deviceId, secret)
        .startClean()
        .withWillQos(MqttQos.atLeastOnce);
    _client.connectionMessage = connMessage;

    try {
      await _client.connect();
    } catch (e) {
      _client.disconnect();
      rethrow;
    }

    _client.subscribe('home/+/telemetry', MqttQos.atMostOnce);
    _client.subscribe('home/+/alert',     MqttQos.exactlyOnce);

    _client.updates!.listen((List<MqttReceivedMessage<MqttMessage>> messages) {
      for (final msg in messages) {
        final pub     = msg.payload as MqttPublishMessage;
        final payload = MqttPublishPayload.bytesToStringAsString(pub.payload.message);
        try {
          final data = json.decode(payload) as Map<String, dynamic>;
          data['_topic'] = msg.topic;
          _telemetryController.add(data);
        } catch (_) {
          // malformed JSON ignored
        }
      }
    });
  }

  void _onConnected()       => print('[MQTT] connected');
  void _onDisconnected()    => print('[MQTT] disconnected');
  void _onAutoReconnected() => print('[MQTT] reconnected');

  void publishCommand(String deviceId, Map<String, dynamic> cmd) {
    final builder = MqttClientPayloadBuilder();
    builder.addString(json.encode(cmd));
    _client.publishMessage(
      'home/$deviceId/cmd/relay',
      MqttQos.atLeastOnce,
      builder.payload!,
    );
  }

  void dispose() {
    _client.disconnect();
    _telemetryController.close();
  }
}
