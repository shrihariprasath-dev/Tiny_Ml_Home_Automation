import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:jwt_decoder/jwt_decoder.dart';

import '../api/api_client.dart';

// ── Events ────────────────────────────────────────────────────────────────────

abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override
  List<Object?> get props => [];
}

class AuthCheckRequested extends AuthEvent {
  const AuthCheckRequested();
}

class AuthLoginRequested extends AuthEvent {
  final String email;
  final String password;
  const AuthLoginRequested({required this.email, required this.password});
  @override
  List<Object?> get props => [email, password];
}

class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

// ── States ────────────────────────────────────────────────────────────────────

abstract class AuthState extends Equatable {
  const AuthState();
  @override
  List<Object?> get props => [];
}

class AuthInitial    extends AuthState { const AuthInitial(); }
class AuthLoading    extends AuthState { const AuthLoading(); }
class AuthAuthenticated extends AuthState {
  final String accessToken;
  const AuthAuthenticated(this.accessToken);
  @override
  List<Object?> get props => [accessToken];
}
class AuthUnauthenticated extends AuthState { const AuthUnauthenticated(); }
class AuthError extends AuthState {
  final String message;
  const AuthError(this.message);
  @override
  List<Object?> get props => [message];
}

// ── BLoC ──────────────────────────────────────────────────────────────────────

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final ApiClient _api;
  final FlutterSecureStorage _storage;

  static const _tokenKey   = 'access_token';
  static const _refreshKey = 'refresh_token';

  AuthBloc(this._api, this._storage) : super(const AuthInitial()) {
    on<AuthCheckRequested>(_onCheck);
    on<AuthLoginRequested>(_onLogin);
    on<AuthLogoutRequested>(_onLogout);
  }

  Future<void> _onCheck(AuthCheckRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    final token = await _storage.read(key: _tokenKey);
    if (token != null && !JwtDecoder.isExpired(token)) {
      emit(AuthAuthenticated(token));
    } else {
      emit(const AuthUnauthenticated());
    }
  }

  Future<void> _onLogin(AuthLoginRequested event, Emitter<AuthState> emit) async {
    emit(const AuthLoading());
    try {
      final data = await _api.login(event.email, event.password);
      await _storage.write(key: _tokenKey,   value: data['access_token']  as String);
      await _storage.write(key: _refreshKey, value: data['refresh_token'] as String);
      emit(AuthAuthenticated(data['access_token'] as String));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }

  Future<void> _onLogout(AuthLogoutRequested event, Emitter<AuthState> emit) async {
    await _storage.deleteAll();
    emit(const AuthUnauthenticated());
  }
}
