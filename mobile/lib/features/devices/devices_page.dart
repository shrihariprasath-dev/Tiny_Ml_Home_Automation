import 'package:flutter/material.dart';

import '../../core/di/service_locator.dart';
import '../../core/api/api_client.dart';
import '../../core/mqtt/mqtt_service.dart';

class DevicesPage extends StatefulWidget {
  const DevicesPage({super.key});

  @override
  State<DevicesPage> createState() => _DevicesPageState();
}

class _DevicesPageState extends State<DevicesPage> {
  final _api  = getIt<ApiClient>();
  final _mqtt = getIt<MqttService>();

  List<Map<String, dynamic>> _devices = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadDevices();
  }

  Future<void> _loadDevices() async {
    try {
      final data = await _api.getDevices();
      setState(() {
        _devices = data.cast<Map<String, dynamic>>();
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _toggleRelay(String deviceId, int relay, bool state) async {
    _mqtt.publishCommand(deviceId, {'relay': relay, 'state': state});
    await _api.controlRelay(deviceId, relay, state);
    setState(() {
      for (final d in _devices) {
        if (d['device_id'] == deviceId) {
          final relays = List<bool>.from(d['relay_states'] as List? ?? [false, false, false, false]);
          relays[relay] = state;
          d['relay_states'] = relays;
        }
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Devices')),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _devices.isEmpty
          ? Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.devices, size: 56, color: Colors.grey.shade300),
                const SizedBox(height: 12),
                const Text('No devices yet', style: TextStyle(color: Colors.grey)),
              ]),
            )
          : RefreshIndicator(
              onRefresh: _loadDevices,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _devices.length,
                itemBuilder: (_, i) => _DeviceCard(
                  device: _devices[i],
                  onToggle: _toggleRelay,
                ),
              ),
            ),
    );
  }
}

class _DeviceCard extends StatelessWidget {
  final Map<String, dynamic> device;
  final Future<void> Function(String, int, bool) onToggle;

  const _DeviceCard({required this.device, required this.onToggle});

  static const _relayLabels = ['Lights', 'Fan', 'AC', 'Spare'];

  @override
  Widget build(BuildContext context) {
    final online      = device['online'] as bool? ?? false;
    final relayStates = List<bool>.from(device['relay_states'] as List? ?? [false, false, false, false]);
    final deviceId    = device['device_id'] as String? ?? '';

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(device['name'] as String? ?? deviceId, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15)),
              Text('${device['room'] ?? "—"} · $deviceId', style: const TextStyle(color: Colors.grey, fontSize: 12)),
            ])),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color:        (online ? Colors.green : Colors.grey).withOpacity(0.12),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                online ? 'Online' : 'Offline',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: online ? Colors.green : Colors.grey),
              ),
            ),
          ]),
          const SizedBox(height: 14),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 8,
              mainAxisSpacing:  8,
              childAspectRatio: 3.2,
            ),
            itemCount: 4,
            itemBuilder: (_, i) => _RelayTile(
              label:    _relayLabels[i],
              state:    relayStates[i],
              disabled: !online,
              onChanged: (v) => onToggle(deviceId, i, v),
            ),
          ),
        ]),
      ),
    );
  }
}

class _RelayTile extends StatelessWidget {
  final String label;
  final bool state, disabled;
  final ValueChanged<bool> onChanged;

  const _RelayTile({required this.label, required this.state, required this.disabled, required this.onChanged});

  @override
  Widget build(BuildContext context) => Container(
    decoration: BoxDecoration(
      color:        state ? Colors.blue.withOpacity(0.08) : Colors.grey.withOpacity(0.06),
      borderRadius: BorderRadius.circular(8),
      border:       Border.all(color: state ? Colors.blue.withOpacity(0.3) : Colors.grey.withOpacity(0.15)),
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Row(children: [
        Expanded(child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500))),
        Switch(value: state, onChanged: disabled ? null : onChanged, materialTapTargetSize: MaterialTapTargetSize.shrinkWrap),
      ]),
    ),
  );
}
