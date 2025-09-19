# flag-llm-prompt.zeek (concept)

event http_request(c: connection, method: string, original_URI: string, unescaped_URI: string, version: string)
{
    if ( /prompt=/ in unescaped_URI ) {
        print fmt("LLM_PROMPT\t%o\t%o", c$id$orig_h, unescaped_URI);
    }
}
