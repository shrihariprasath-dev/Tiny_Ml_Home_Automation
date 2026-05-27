import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../auth/auth_bloc.dart';
import '../../features/auth/login_page.dart';
import '../../features/dashboard/dashboard_page.dart';
import '../../features/devices/devices_page.dart';
import '../../features/alerts/alerts_page.dart';

final appRouter = GoRouter(
  initialLocation: '/dashboard',
  redirect: (context, state) {
    final authState = context.read<AuthBloc>().state;
    final isAuth    = authState is AuthAuthenticated;
    final isLogin   = state.matchedLocation == '/login';
    if (!isAuth && !isLogin) return '/login';
    if (isAuth  &&  isLogin) return '/dashboard';
    return null;
  },
  routes: [
    GoRoute(path: '/login',     builder: (_, __) => const LoginPage()),
    ShellRoute(
      builder: (context, state, child) => ScaffoldWithNav(child: child),
      routes: [
        GoRoute(path: '/dashboard', builder: (_, __) => const DashboardPage()),
        GoRoute(path: '/devices',   builder: (_, __) => const DevicesPage()),
        GoRoute(path: '/alerts',    builder: (_, __) => const AlertsPage()),
      ],
    ),
  ],
);

class ScaffoldWithNav extends StatelessWidget {
  final Widget child;
  const ScaffoldWithNav({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: switch (location) {
          '/dashboard' => 0,
          '/devices'   => 1,
          '/alerts'    => 2,
          _            => 0,
        },
        onDestinationSelected: (i) => switch (i) {
          0 => context.go('/dashboard'),
          1 => context.go('/devices'),
          2 => context.go('/alerts'),
          _ => context.go('/dashboard'),
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined),        selectedIcon: Icon(Icons.home),        label: 'Home'),
          NavigationDestination(icon: Icon(Icons.devices_outlined),     selectedIcon: Icon(Icons.devices),     label: 'Devices'),
          NavigationDestination(icon: Icon(Icons.notifications_outlined),selectedIcon: Icon(Icons.notifications),label: 'Alerts'),
        ],
      ),
    );
  }
}
