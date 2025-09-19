# zeek/scripts/log-long-requests-json.zeek
@load base/protocols/http

redef LogAscii::use_json = T;

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    if ( c?$http && c$http?$body_length && c$http$body_length > 1024 ) {
        local rec = {
            ts: network_time(),
            src: c$id$orig_h,
            dst: c$id$resp_h,
            uri: unescaped_URI,
            body_length: c$http$body_length,
            note: "long_request"
        };
        print fmt("%s", to_json(rec));
    }
}
