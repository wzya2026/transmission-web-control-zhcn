/* Desktop detail layout for Transmission Web Control. MIT, wzya2026. */
(function (root, $) {
    "use strict";
    var system = root.system;
    if (!system || !$) return;
    function value(id, text) { $("#desktop-detail-" + id).text(text == null ? "—" : text); }
    function duration(seconds) {
        seconds = Math.max(0, Math.floor(Number(seconds) || 0));
        var days = Math.floor(seconds / 86400), hours = Math.floor(seconds / 3600) % 24, minutes = Math.floor(seconds / 60) % 60;
        return (days ? days + " 天 " : "") + (hours ? hours + " 小时 " : "") + minutes + " 分钟";
    }
    function summary(torrent) {
        if (!torrent) {
            value("name", "点选上方任务，查看详细信息"); value("status", "未选择任务");
            ["size", "completed", "download", "upload", "ratio"].forEach(function (key) { value(key, "—"); });
            $("#desktop-detail-progress").attr("aria-valuenow", 0).find("span").css("width", "0%");
            return;
        }
        var percent = Math.min(100, Math.max(0, (Number(torrent.percentDone) || 0) * 100));
        value("name", torrent.name);
        $("#desktop-detail-name").attr("title", torrent.name || "");
        value("status", (system.lang.torrent["status-text"][torrent.status] || "") + " · " + percent.toFixed(1) + "%");
        value("size", root.formatSize(Number(torrent.totalSize) || 0));
        value("completed", root.formatSize(Math.max(0, (Number(torrent.totalSize) || 0) - (Number(torrent.leftUntilDone) || 0))));
        value("download", root.formatSize(Number(torrent.rateDownload) || 0, false, "speed"));
        value("upload", root.formatSize(Number(torrent.rateUpload) || 0, false, "speed"));
        value("ratio", Number(torrent.uploadRatio) < 0 ? "—" : Number(torrent.uploadRatio || 0).toFixed(2));
        $("#desktop-detail-progress").attr("aria-valuenow", percent.toFixed(1)).find("span").css("width", percent + "%");
    }
    system.showDesktopDetails = function (torrent) {
        if (!this.panel || !this.panel.attribute) return;
        var changed = this.currentTorrentId !== torrent.id;
        this.currentTorrentId = torrent.id;
        if (changed) this.clearTorrentAttribute();
        summary(root.transmission.torrents.all[torrent.id] || torrent);
        if (this.panel.attribute.panel("options").collapsed) this.panel.layout_body.layout("expand", "south");
    };
    var init = system.initUIStatus;
    system.ensureDesktopInitialSelection = function () {
        if (this.desktopListReady || !this.lang || !root.transmission.torrents.all || !this.control.torrentlist || !this.control.torrentlist.data("datagrid")) return;
        var node = this.panel.left.tree("getSelected");
        if (!node) node = this.panel.left.tree("find", this.config.defaultSelectNode) || this.panel.left.tree("find", "torrent-all");
        if (!node) return;
        this.desktopListReady = true;
        this.panel.left.tree("select", node.target);
    };
    system.initUIStatus = function () {
        if (this.config.defaultSelectNode === "all") this.config.defaultSelectNode = "torrent-all";
        var result = init.apply(this, arguments);
        this.ensureDesktopInitialSelection();
        if (!this.uiIsInitialized || this.desktopDetailsInitialized) return result;
        this.desktopDetailsInitialized = true;
        var saved = this.lastUIStatus.size.attribute && Number(this.lastUIStatus.size.attribute.height);
        var maximum = Math.max(180, Math.floor(root.innerHeight * 0.65));
        var height = saved > 180 ? Math.min(saved, maximum) : Math.min(420, Math.max(260, Math.floor(root.innerHeight * 0.43)));
        this.panel.layout_body.layout("panel", "south").panel("resize", { height: height });
        this.panel.layout_body.layout("expand", "south");
        this.panel.layout_body.layout("resize");
        summary(null);
        return result;
    };
    var fill = system.fillTorrentBaseInfos;
    system.fillTorrentBaseInfos = function (torrent) {
        var result = fill.apply(this, arguments);
        summary(torrent);
        var extra = {
            downloadedEver: root.formatSize(Number(torrent.downloadedEver) || 0),
            secondsDownloading: duration(torrent.secondsDownloading),
            secondsSeeding: duration(torrent.secondsSeeding),
            isPrivate: torrent.isPrivate ? "是" : "否"
        };
        Object.keys(extra).forEach(function (key) { $("#torrent-attribute-value-" + key).text(extra[key]); });
        return result;
    };
    var clear = system.clearTorrentAttribute;
    system.clearTorrentAttribute = function () {
        var result = clear.apply(this, arguments);
        summary(null);
        return result;
    };
    root.TWCDesktopDetails = { duration: duration };
})(window, window.jQuery);
