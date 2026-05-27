import 'package:flutter/material.dart';

class AppTheme {
  static const _primary = Color(0xFF2563EB);
  static const _error   = Color(0xFFEF4444);

  static ThemeData get light => ThemeData(
    useMaterial3:    true,
    colorSchemeSeed: _primary,
    brightness:      Brightness.light,
    fontFamily:      'Inter',
    appBarTheme: const AppBarTheme(
      elevation:          0,
      scrolledUnderElevation: 0,
      backgroundColor:    Colors.white,
      foregroundColor:    Color(0xFF111827),
      titleTextStyle: TextStyle(
        color:      Color(0xFF111827),
        fontSize:   17,
        fontWeight: FontWeight.w600,
        fontFamily: 'Inter',
      ),
    ),
    cardTheme: CardThemeData(
      elevation:    0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side:         const BorderSide(color: Color(0xFFE5E7EB)),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border:        OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      filled:        true,
      fillColor:     const Color(0xFFF9FAFB),
    ),
    colorScheme: ColorScheme.fromSeed(
      seedColor:  _primary,
      brightness: Brightness.light,
      error:      _error,
    ),
  );

  static ThemeData get dark => ThemeData(
    useMaterial3:    true,
    colorSchemeSeed: _primary,
    brightness:      Brightness.dark,
    fontFamily:      'Inter',
  );
}
