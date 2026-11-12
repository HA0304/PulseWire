SLOW_START_REFERENCE = (
    {"time": 0.0, "event": "ack", "cwnd": 2.0, "ssthresh": 8.0},
    {"time": 1.0, "event": "ack", "cwnd": 3.0, "ssthresh": 8.0},
    {"time": 2.0, "event": "ack", "cwnd": 4.0, "ssthresh": 8.0},
)

TIMEOUT_REFERENCE = (
    {"time": 3.0, "event": "timeout", "cwnd": 1.0, "ssthresh": 4.0},
)

TRIPLE_DUPLICATE_ACK_REFERENCE = (
    {"time": 4.0, "event": "triple_duplicate_ack", "cwnd": 4.0, "ssthresh": 4.0},
)
