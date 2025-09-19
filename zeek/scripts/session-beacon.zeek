# session-beacon.zeek (concept)

global recent_req_count: table[count] of count = {};

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    local src = c$id$orig_h;
    if ( ! (src in recent_req_count) )
        recent_req_count[src] = 0;
    recent_req_count[src] += 1;
    if ( recent_req_count[src] > 20 ) {
        print fmt("BEACON_DETECT\t%o\t%o", src, recent_req_count[src]);
        recent_req_count[src] = 0; # reset window simplification
    }
}
