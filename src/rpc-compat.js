/* Transmission Web Control community continuation.
 * Upstream UI: ronggang/transmission-web-control (MIT).
 * Protocol boundary for Transmission 4.1 JSON-RPC; old daemons retain legacy RPC.
 */
(function (root) {
    "use strict";
    function snake(key) {
        return key.replace(/([a-z0-9])([A-Z])/g, "$1_$2").replace(/-/g, "_").toLowerCase();
    }
    function camel(key) { return key.replace(/_([a-z])/g, function (_, c) { return c.toUpperCase(); }); }
    function encodeArguments(value, parent) {
        if (Array.isArray(value)) {
            return value.map(function (item) { return parent === "fields" && typeof item === "string" ? snake(item) : encodeArguments(item, parent); });
        }
        if (!value || typeof value !== "object") {
            if (parent === "ids" && value === "recently-active") { return "recently_active"; }
            return parent === "encryption" && value === "tolerated" ? "allowed" : value;
        }
        var out = {};
        Object.keys(value).forEach(function (key) {
            var normalized = key === "cache-size-mb" ? "cache_size_mib" : snake(key);
            out[normalized] = encodeArguments(value[key], normalized);
        });
        return out;
    }
    function decodeResult(method, value, parent) {
        if (Array.isArray(value)) {
            return value.map(function (item) { return parent === "wanted" && typeof item === "boolean" ? (item ? 1 : 0) : decodeResult(method, item, parent); });
        }
        if (!value || typeof value !== "object") { return parent === "encryption" && value === "allowed" ? "tolerated" : value; }
        var out = {}, session = method === "session-get", stats = method === "session-stats";
        Object.keys(value).forEach(function (key) {
            var legacy;
            if (session) {
                legacy = key === "cache_size_mib" ? "cache-size-mb" : key === "seed_ratio_limit" ? "seedRatioLimit" : key === "seed_ratio_limited" ? "seedRatioLimited" : key.replace(/_/g, "-");
            }
            else if (stats && (key === "cumulative_stats" || key === "current_stats")) { legacy = key.replace(/_/g, "-"); }
            else if (method === "torrent-add" && (key === "torrent_added" || key === "torrent_duplicate")) { legacy = key.replace(/_/g, "-"); }
            else if (method === "free-space") { legacy = key === "size_bytes" ? "size-bytes" : key; }
            else if (method === "port-test" || method === "blocklist-update") { legacy = key.replace(/_/g, "-"); }
            else { legacy = key === "peer_limit" ? "peer-limit" : camel(key); }
            out[legacy] = decodeResult(method, value[key], key);
        });
        return out;
    }
    var compatibility = { snake: snake, encodeArguments: encodeArguments, decodeResult: decodeResult };
    if (typeof module === "object" && module.exports) { module.exports = compatibility; }
    root.TWCCompatibility = compatibility;
    if (!root.transmission || !root.jQuery) { return; }
    var tr = root.transmission, jq = root.jQuery, legacyExec = tr.exec;
    tr.rpcVersionSemver = "";
    tr.modernRpc = false;
    tr.requestSequence = 0;
    tr.getSessionId = function (me, callback) {
        jq.ajax({ type: "POST", url: me.fullpath, headers: me.headers, error: function (request) {
            var id = request.getResponseHeader("X-Transmission-Session-Id");
            if (request.status === 409 && id) {
                me.SessionId = id; me.headers["X-Transmission-Session-Id"] = id; me.isInitialized = true;
                me.rpcVersionSemver = request.getResponseHeader("X-Transmission-Rpc-Version") || "";
                me.modernRpc = parseInt(me.rpcVersionSemver.split(".")[0], 10) >= 6;
                if (callback) { callback(); }
            } else if (me.on.postError) { me.on.postError(request); }
        }});
    };
    tr.exec = function (config, callback, tags) {
        if (!this.modernRpc) { return legacyExec.call(this, config, callback, tags); }
        if (!this.isInitialized) { return false; }
        var me = this, method = config.method, retried = false;
        var requestData = { jsonrpc: "2.0", id: ++me.requestSequence, method: snake(method), params: encodeArguments(config.arguments || {}) };
        var settings = { type: "POST", url: me.fullpath, contentType: "application/json", dataType: "json", headers: me.headers, data: JSON.stringify(requestData),
            success: function (data) {
                var result = data.error ? { result: data.error.message || "RPC error", arguments: {} } : { result: "success", arguments: decodeResult(method, data.result || {}) };
                if (config.tag !== undefined) { result.tag = config.tag; }
                if (callback) { callback(result, tags); }
            },
            error: function (request) {
                var id = request.getResponseHeader("X-Transmission-Session-Id");
                if (request.status === 409 && id && !retried) {
                    retried = true; me.SessionId = id; me.headers["X-Transmission-Session-Id"] = id; jq.ajax(settings);
                } else if (me.on.postError) { me.on.postError(request); }
            }
        };
        return jq.ajax(settings);
    };
})(typeof window !== "undefined" ? window : globalThis);
