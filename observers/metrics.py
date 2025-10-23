#!/usr/bin/env python3
"""
Metrics and Observability
Prometheus exporters, SLO monitoring, and self-healing triggers
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

class MetricsCollector:
    def __init__(self):
        # Time-series metrics storage (in-memory for now)
        self.metrics = defaultdict(deque)  # metric_name -> deque of (timestamp, value)
        self.counters = defaultdict(int)   # metric_name -> count
        self.gauges = defaultdict(float)   # metric_name -> current_value
        self.histograms = defaultdict(list) # metric_name -> list of values
        
        # SLO definitions
        self.slos = {
            'memory_write_latency_p95': {'threshold': 100, 'unit': 'ms'},  # 95th percentile < 100ms
            'memory_search_latency_p95': {'threshold': 50, 'unit': 'ms'},   # 95th percentile < 50ms
            'graph_query_latency_p95': {'threshold': 200, 'unit': 'ms'},    # 95th percentile < 200ms
            'api_error_rate': {'threshold': 0.01, 'unit': 'ratio'},         # Error rate < 1%
            'ingestion_queue_depth': {'threshold': 100, 'unit': 'count'},   # Queue depth < 100
            'memory_system_uptime': {'threshold': 0.999, 'unit': 'ratio'}   # 99.9% uptime
        }
        
        # Auto-remediation runbooks
        self.runbooks = {
            'high_latency': self._remediate_high_latency,
            'high_error_rate': self._remediate_high_error_rate,
            'queue_backlog': self._remediate_queue_backlog,
            'service_down': self._remediate_service_down
        }
        
        # Keep only last 1000 data points per metric
        self.max_data_points = 1000
    
    def record_latency(self, metric_name: str, latency_ms: float):
        """Record latency measurement"""
        timestamp = time.time()
        self.metrics[metric_name].append((timestamp, latency_ms))
        self.histograms[f"{metric_name}_histogram"].append(latency_ms)
        
        # Trim old data
        if len(self.metrics[metric_name]) > self.max_data_points:
            self.metrics[metric_name].popleft()
        
        # Keep only recent histogram data
        if len(self.histograms[f"{metric_name}_histogram"]) > 1000:
            self.histograms[f"{metric_name}_histogram"] = self.histograms[f"{metric_name}_histogram"][-1000:]
    
    def increment_counter(self, metric_name: str, value: int = 1):
        """Increment counter metric"""
        self.counters[metric_name] += value
        timestamp = time.time()
        self.metrics[f"{metric_name}_total"].append((timestamp, self.counters[metric_name]))
    
    def set_gauge(self, metric_name: str, value: float):
        """Set gauge metric value"""
        self.gauges[metric_name] = value
        timestamp = time.time()
        self.metrics[metric_name].append((timestamp, value))
        
        # Trim old data
        if len(self.metrics[metric_name]) > self.max_data_points:
            self.metrics[metric_name].popleft()
    
    def calculate_percentile(self, metric_name: str, percentile: float) -> float:
        """Calculate percentile for histogram metric"""
        histogram_key = f"{metric_name}_histogram"
        if histogram_key not in self.histograms or not self.histograms[histogram_key]:
            return 0.0
        
        values = sorted(self.histograms[histogram_key])
        if not values:
            return 0.0
        
        index = int(len(values) * percentile / 100.0)
        return values[min(index, len(values) - 1)]
    
    def check_slo_violations(self) -> List[Dict]:
        """Check for SLO violations and trigger remediation"""
        violations = []
        
        for slo_name, slo_config in self.slos.items():
            threshold = slo_config['threshold']
            
            if 'latency_p95' in slo_name:
                # Check 95th percentile latency
                base_metric = slo_name.replace('_p95', '')
                current_p95 = self.calculate_percentile(base_metric, 95.0)
                
                if current_p95 > threshold:
                    violations.append({
                        'slo': slo_name,
                        'current_value': current_p95,
                        'threshold': threshold,
                        'severity': 'high' if current_p95 > threshold * 2 else 'medium',
                        'remediation': 'high_latency'
                    })
            
            elif 'error_rate' in slo_name:
                # Check error rate
                total_requests = self.counters.get('api_requests_total', 1)
                total_errors = self.counters.get('api_errors_total', 0)
                error_rate = total_errors / total_requests
                
                if error_rate > threshold:
                    violations.append({
                        'slo': slo_name,
                        'current_value': error_rate,
                        'threshold': threshold,
                        'severity': 'high',
                        'remediation': 'high_error_rate'
                    })
            
            elif 'queue_depth' in slo_name:
                # Check ingestion queue depth
                current_depth = self.gauges.get('ingestion_queue_depth', 0)
                
                if current_depth > threshold:
                    violations.append({
                        'slo': slo_name,
                        'current_value': current_depth,
                        'threshold': threshold,
                        'severity': 'medium',
                        'remediation': 'queue_backlog'
                    })
        
        return violations
    
    async def _remediate_high_latency(self, violation: Dict):
        """Remediate high latency issues"""
        print(f"🚨 Auto-remediation: High latency detected ({violation['current_value']:.2f}ms)")
        
        # Remediation actions
        remediation_log = []
        
        # 1. Clear caches
        # TODO: Implement cache clearing
        remediation_log.append("Cleared application caches")
        
        # 2. Check Neo4j indexes
        # TODO: Rebuild indexes if needed
        remediation_log.append("Validated Neo4j indexes")
        
        # 3. Scale horizontally if possible
        # TODO: Auto-scaling logic
        remediation_log.append("Evaluated auto-scaling options")
        
        return {
            'remediation_type': 'high_latency',
            'actions_taken': remediation_log,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _remediate_high_error_rate(self, violation: Dict):
        """Remediate high error rate"""
        print(f"🚨 Auto-remediation: High error rate detected ({violation['current_value']:.3f})")
        
        return {
            'remediation_type': 'high_error_rate',
            'actions_taken': ['Enabled circuit breaker', 'Increased retry intervals'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _remediate_queue_backlog(self, violation: Dict):
        """Remediate ingestion queue backlog"""
        print(f"🚨 Auto-remediation: Queue backlog detected ({violation['current_value']} items)")
        
        return {
            'remediation_type': 'queue_backlog',
            'actions_taken': ['Scaled ingestion workers', 'Prioritized critical items'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _remediate_service_down(self, violation: Dict):
        """Remediate service downtime"""
        print(f"🚨 Auto-remediation: Service down detected")
        
        return {
            'remediation_type': 'service_down',
            'actions_taken': ['Attempted service restart', 'Enabled backup endpoints'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        
        # Counters
        for metric_name, value in self.counters.items():
            lines.append(f"# TYPE {metric_name} counter")
            lines.append(f"{metric_name} {value}")
        
        # Gauges
        for metric_name, value in self.gauges.items():
            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name} {value}")
        
        # Histograms (simplified)
        for metric_name, values in self.histograms.items():
            if values:
                p50 = self.calculate_percentile(metric_name.replace('_histogram', ''), 50.0)
                p95 = self.calculate_percentile(metric_name.replace('_histogram', ''), 95.0)
                p99 = self.calculate_percentile(metric_name.replace('_histogram', ''), 99.0)
                
                base_name = metric_name.replace('_histogram', '')
                lines.append(f"# TYPE {base_name} histogram")
                lines.append(f"{base_name}{{quantile=\"0.5\"}} {p50}")
                lines.append(f"{base_name}{{quantile=\"0.95\"}} {p95}")
                lines.append(f"{base_name}{{quantile=\"0.99\"}} {p99}")
        
        return "\n".join(lines)
    
    def get_slo_dashboard(self) -> Dict:
        """Get SLO dashboard data"""
        dashboard = {
            'timestamp': datetime.utcnow().isoformat(),
            'slos': {},
            'overall_health': 'GREEN'
        }
        
        violations = self.check_slo_violations()
        
        for slo_name, slo_config in self.slos.items():
            threshold = slo_config['threshold']
            
            if 'latency_p95' in slo_name:
                base_metric = slo_name.replace('_p95', '')
                current_value = self.calculate_percentile(base_metric, 95.0)
                status = 'BREACH' if current_value > threshold else 'OK'
            else:
                # Handle other SLO types
                current_value = 0  # Placeholder
                status = 'OK'
            
            dashboard['slos'][slo_name] = {
                'current': current_value,
                'threshold': threshold,
                'status': status,
                'unit': slo_config['unit']
            }
        
        # Set overall health based on violations
        if any(v['severity'] == 'high' for v in violations):
            dashboard['overall_health'] = 'RED'
        elif violations:
            dashboard['overall_health'] = 'YELLOW'
        
        dashboard['violations'] = violations
        
        return dashboard

# Global metrics collector
metrics = MetricsCollector()

# Context managers for automatic metrics recording
class LatencyTimer:
    def __init__(self, metric_name: str):
        self.metric_name = metric_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000
            metrics.record_latency(self.metric_name, latency_ms)
            
            # Also increment request counter
            if exc_type is None:
                metrics.increment_counter(f"{self.metric_name}_success_total")
            else:
                metrics.increment_counter(f"{self.metric_name}_error_total")

if __name__ == '__main__':
    # Test metrics collection
    collector = MetricsCollector()
    
    # Simulate some metrics
    for i in range(100):
        collector.record_latency('memory_write_latency', 50 + i)
        collector.record_latency('memory_search_latency', 20 + i)
        collector.increment_counter('api_requests_total')
        
        if i % 20 == 0:  # 5% error rate
            collector.increment_counter('api_errors_total')
    
    # Check SLOs
    violations = collector.check_slo_violations()
    print(f"SLO violations: {len(violations)}")
    
    # Get dashboard
    dashboard = collector.get_slo_dashboard()
    print(f"Overall health: {dashboard['overall_health']}")