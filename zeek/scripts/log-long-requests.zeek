# log-long-requests.zeek (concept)

module TheFool::HTTP;

export {
    redef enum Log::ID += { LOG_LONG_REQUESTS };
}

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    if ( c?$http && c$http?$body_length && c$http$body_length > 1024 ) {
        # write to a custom log (implementation detail simplified)
        print fmt("LONG_REQ\t%o\t%o\t%o", c$id$orig_h, unescaped_URI, c$http$body_length);
    }
}
