import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';

import '../api/api_client.dart';
import '../mqtt/mqtt_service.dart';
import '../auth/auth_bloc.dart';

final getIt = GetIt.instance;

void setupServiceLocator() {
  getIt.registerLazySingleton<FlutterSecureStorage>(
    () => const FlutterSecureStorage(),
  );

  getIt.registerLazySingleton<ApiClient>(
    () => ApiClient(getIt<FlutterSecureStorage>()),
  );

  getIt.registerLazySingleton<MqttService>(() => MqttService());

  getIt.registerFactory<AuthBloc>(
    () => AuthBloc(getIt<ApiClient>(), getIt<FlutterSecureStorage>()),
  );
}
