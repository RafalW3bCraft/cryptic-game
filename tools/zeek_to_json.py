#!/usr/bin/env python3
# tools/zeek_to_json.py
# Tail a Zeek http.log (tab-separated) and write JSON lines for HTTP requests with body_len > threshold.
# Usage:
#   python3 tools/zeek_to_json.py --zeek-log ./zeek/logs/current/http.log --out ./zeek/logs/long_requests.jsonl --threshold 1024

import argparse, json, time, os, sys

def parse_zeek_http_line(line):
    # Zeek http.log is tab-separated with a header table; this parser is a pragmatic heuristic.
    parts = line.rstrip('\n').split('\t')
    # Basic guard: typical Zeek http.log has many fields; we need at least indices for src/dst/uri/body_len
    if len(parts) < 14:
        return None
    try:
        rec = {
            'ts': parts[0],
            'uid': parts[1],
            'src': parts[2],
            'src_port': parts[3],
            'dst': parts[4],
            'dst_port': parts[5],
            'method': parts[7] if len(parts) > 7 else '',
            'host': parts[8] if len(parts) > 8 else '',
            'uri': parts[9] if len(parts) > 9 else '',
            'request_body_len': int(parts[12]) if parts[12].isdigit() else 0,
            'response_body_len': int(parts[13]) if parts[13].isdigit() else 0,
        }
        return rec
    except Exception:
        return None

def follow(thefile):
    thefile.seek(0, os.SEEK_END)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.5)
            continue
        yield line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zeek-log', default='./zeek/logs/current/http.log', help='Path to Zeek http.log (current)')
    parser.add_argument('--out', default='./zeek/logs/long_requests.jsonl', help='Output JSONL path')
    parser.add_argument('--threshold', type=int, default=1024, help='Request body length threshold in bytes')
    args = parser.parse_args()

    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    try:
        with open(args.zeek_log, 'r', encoding='utf-8', errors='ignore') as fh, open(args.out, 'a', encoding='utf-8') as outfh:
            for line in follow(fh):
                rec = parse_zeek_http_line(line)
                if not rec:
                    continue
                if rec.get('request_body_len', 0) > args.threshold:
                    outfh.write(json.dumps({
                        'ts': rec['ts'],
                        'src': rec['src'],
                        'dst': rec['dst'],
                        'uri': rec['uri'],
                        'request_body_len': rec['request_body_len']
                    }) + '\\n')
                    outfh.flush()
    except FileNotFoundError:
        print('Zeek log not found at', args.zeek_log, file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()
