import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../core/di/service_locator.dart';
import '../../core/api/api_client.dart';

class AlertsPage extends StatefulWidget {
  const AlertsPage({super.key});

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  final _api = getIt<ApiClient>();

  List<Map<String, dynamic>> _alerts  = [];
  bool _loading  = true;
  bool _showAll  = false;

  @override
  void initState() {
    super.initState();
    _loadAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() => _loading = true);
    try {
      final data = await _api.getAlerts(acknowledgedOnly: _showAll);
      setState(() {
        _alerts  = data.cast<Map<String, dynamic>>();
        _loading = false;
      });
    } catch (_) {
      setState(() => _loading = false);
    }
  }

  Future<void> _acknowledge(String id) async {
    await _api.acknowledgeAlert(id);
    setState(() {
      for (final a in _alerts) {
        if (a['id'] == id) a['acknowledged_at'] = DateTime.now().toIso8601String();
      }
    });
  }

  static const _severityColors = {
    'low':      Colors.blue,
    'medium':   Colors.orange,
    'high':     Colors.deepOrange,
    'critical': Colors.red,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerts'),
        actions: [
          TextButton(
            onPressed: () { setState(() => _showAll = !_showAll); _loadAlerts(); },
            child: Text(_showAll ? 'Unread' : 'All', style: const TextStyle(color: Colors.blue)),
          ),
        ],
      ),
      body: _loading
        ? const Center(child: CircularProgressIndicator())
        : _alerts.isEmpty
          ? Center(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.notifications_off_outlined, size: 56, color: Colors.grey.shade300),
                const SizedBox(height: 12),
                Text(_showAll ? 'No alerts' : 'No unread alerts', style: const TextStyle(color: Colors.grey)),
              ]),
            )
          : RefreshIndicator(
              onRefresh: _loadAlerts,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _alerts.length,
                itemBuilder: (_, i) {
                  final a         = _alerts[i];
                  final severity  = a['severity'] as String? ?? 'low';
                  final color     = _severityColors[severity] ?? Colors.grey;
                  final acked     = a['acknowledged_at'] != null;
                  final createdAt = DateTime.tryParse(a['created_at'] as String? ?? '');

                  return Opacity(
                    opacity: acked ? 0.55 : 1.0,
                    child: Card(
                      margin: const EdgeInsets.only(bottom: 10),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: color.withOpacity(0.1),
                          child: Icon(Icons.warning_amber_rounded, color: color, size: 20),
                        ),
                        title: Text(a['message'] as String? ?? '', style: const TextStyle(fontSize: 13)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const SizedBox(height: 2),
                            Row(children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
                                child: Text(severity.toUpperCase(), style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: color)),
                              ),
                              const SizedBox(width: 6),
                              Text(a['device_id'] as String? ?? '', style: const TextStyle(fontSize: 11, color: Colors.grey)),
                            ]),
                            if (createdAt != null) ...[
                              const SizedBox(height: 2),
                              Text(DateFormat('MMM d, HH:mm').format(createdAt.toLocal()), style: const TextStyle(fontSize: 11, color: Colors.grey)),
                            ],
                          ],
                        ),
                        trailing: !acked
                          ? TextButton(
                              onPressed: () => _acknowledge(a['id'] as String),
                              child: const Text('ACK', style: TextStyle(fontSize: 11)),
                            )
                          : const Icon(Icons.check_circle_outline, color: Colors.green, size: 18),
                        isThreeLine: true,
                      ),
                    ),
                  );
                },
              ),
            ),
    );
  }
}
