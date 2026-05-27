import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

import '../../core/di/service_locator.dart';
import '../../core/api/api_client.dart';
import '../../core/mqtt/mqtt_service.dart';

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  final _api      = getIt<ApiClient>();
  final _mqtt     = getIt<MqttService>();
  StreamSubscription? _mqttSub;

  double _powerW       = 0;
  double _voltage      = 0;
  double _energyKwh    = 0;
  double _temperature  = 0;
  double _anomalyScore = 0;
  double _occupancyPct = 0;
  final List<FlSpot> _powerHistory = [];
  int    _historyIdx   = 0;

  @override
  void initState() {
    super.initState();
    _mqttSub = _mqtt.telemetryStream.listen(_onTelemetry);
  }

  void _onTelemetry(Map<String, dynamic> data) {
    if (!mounted) return;
    setState(() {
      _powerW       = (data['power_w']        as num?)?.toDouble() ?? _powerW;
      _voltage      = (data['voltage']        as num?)?.toDouble() ?? _voltage;
      _energyKwh    = (data['energy_kwh']     as num?)?.toDouble() ?? _energyKwh;
      _temperature  = (data['temperature']    as num?)?.toDouble() ?? _temperature;
      _anomalyScore = (data['anomaly_score']  as num?)?.toDouble() ?? _anomalyScore;
      _occupancyPct = ((data['occupancy_prob'] as num?)?.toDouble() ?? 0) * 100;

      _powerHistory.add(FlSpot(_historyIdx.toDouble(), _powerW));
      if (_powerHistory.length > 60) _powerHistory.removeAt(0);
      _historyIdx++;
    });
  }

  @override
  void dispose() {
    _mqttSub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Overview')),
      body: RefreshIndicator(
        onRefresh: () async {},
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _KpiGrid(
              powerW:      _powerW,
              voltage:     _voltage,
              energyKwh:   _energyKwh,
              temperature: _temperature,
            ),
            const SizedBox(height: 16),
            _PowerChart(spots: _powerHistory),
            const SizedBox(height: 16),
            Row(children: [
              Expanded(child: _AnomalyCard(score: _anomalyScore)),
              const SizedBox(width: 12),
              Expanded(child: _OccupancyCard(pct: _occupancyPct)),
            ]),
          ],
        ),
      ),
    );
  }
}

class _KpiGrid extends StatelessWidget {
  final double powerW, voltage, energyKwh, temperature;
  const _KpiGrid({required this.powerW, required this.voltage, required this.energyKwh, required this.temperature});

  @override
  Widget build(BuildContext context) => GridView.count(
    crossAxisCount: 2,
    shrinkWrap: true,
    physics: const NeverScrollableScrollPhysics(),
    crossAxisSpacing: 12,
    mainAxisSpacing: 12,
    childAspectRatio: 1.6,
    children: [
      _KpiTile(label: 'Power',       value: '${powerW.toStringAsFixed(0)} W',       icon: Icons.bolt,        color: Colors.blue),
      _KpiTile(label: 'Voltage',     value: '${voltage.toStringAsFixed(1)} V',       icon: Icons.electric_bolt, color: Colors.orange),
      _KpiTile(label: 'Today kWh',   value: energyKwh.toStringAsFixed(3),            icon: Icons.energy_savings_leaf, color: Colors.green),
      _KpiTile(label: 'Temperature', value: '${temperature.toStringAsFixed(1)} °C',  icon: Icons.thermostat,  color: Colors.red),
    ],
  );
}

class _KpiTile extends StatelessWidget {
  final String label, value;
  final IconData icon;
  final Color color;
  const _KpiTile({required this.label, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Row(children: [
        CircleAvatar(backgroundColor: color.withOpacity(0.1), child: Icon(icon, color: color, size: 20)),
        const SizedBox(width: 10),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment:  MainAxisAlignment.center,
          children: [
            Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
            Text(value,  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          ],
        )),
      ]),
    ),
  );
}

class _PowerChart extends StatelessWidget {
  final List<FlSpot> spots;
  const _PowerChart({required this.spots});

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('Live Power (W)', style: Theme.of(context).textTheme.titleSmall),
        const SizedBox(height: 12),
        SizedBox(
          height: 140,
          child: spots.isEmpty
            ? const Center(child: Text('Waiting for data…', style: TextStyle(color: Colors.grey)))
            : LineChart(LineChartData(
                gridData:     FlGridData(show: true, drawVerticalLine: false),
                borderData:   FlBorderData(show: false),
                titlesData:   FlTitlesData(
                  leftTitles:   AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40)),
                  bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  topTitles:    AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles:  AxisTitles(sideTitles: SideTitles(showTitles: false)),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots:          spots,
                    isCurved:       true,
                    color:          Colors.blue,
                    barWidth:       2,
                    dotData:        FlDotData(show: false),
                    belowBarData:   BarAreaData(show: true, color: Colors.blue.withOpacity(0.1)),
                  ),
                ],
              )),
        ),
      ]),
    ),
  );
}

class _AnomalyCard extends StatelessWidget {
  final double score;
  const _AnomalyCard({required this.score});

  @override
  Widget build(BuildContext context) {
    final color = score > 0.5 ? Colors.red : score > 0.3 ? Colors.orange : Colors.green;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Icon(Icons.warning_amber_rounded, color: color, size: 16), const SizedBox(width: 4), const Text('Anomaly', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13))]),
          const SizedBox(height: 8),
          Text(score.toStringAsFixed(3), style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
          Text(score > 0.5 ? 'DETECTED' : 'Normal', style: TextStyle(fontSize: 11, color: color)),
        ]),
      ),
    );
  }
}

class _OccupancyCard extends StatelessWidget {
  final double pct;
  const _OccupancyCard({required this.pct});

  @override
  Widget build(BuildContext context) {
    final occupied = pct >= 60;
    final color    = occupied ? Colors.green : Colors.grey;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [Icon(Icons.people_outline, color: color, size: 16), const SizedBox(width: 4), const Text('Occupancy', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13))]),
          const SizedBox(height: 8),
          Text('${pct.toStringAsFixed(0)}%', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
          Text(occupied ? 'Occupied' : 'Empty', style: TextStyle(fontSize: 11, color: color)),
        ]),
      ),
    );
  }
}
