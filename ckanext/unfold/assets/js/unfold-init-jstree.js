ckan.module("unfold-init-jstree", function ($, _) {
    "use strict";
    return {
        options: {
            resourceId: null,
            resourceViewId: null,
            animationThreshold: 1000,
            searchShowOnlyMatches: true,
            searchCloseOpenedOnClear: false,
            searchLimit: 200,
            pageSize: 500,
            showContextMenu: true,
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            this.tree = $(this.el);
            this.errorBlock = $("#archive-tree-error");
            this.loadState = $(".unfold-load-state");
            this.meta = $(".unfold-tree-meta");
            this.expandAll = $("#jstree-expand-all");
            this.results = $("#archive-search-results");
            // "full": every node is in the DOM; "lazy": folders load on open
            this.mode = null;
            this.total = 0;
            // lazy mode: how many children each folder currently shows
            this.folderLimits = {};

            $("#jstree-search").on("change", (e) => this._search($(e.target).val()));
            $("#jstree-search-run").click(() => this._search($("#jstree-search").val()));
            $("#jstree-search-clear").click(() => {
                $("#jstree-search").val("");
                this._clearSearch();
            });
            this.expandAll.click(() => this.tree.jstree("open_all"));
            $("#jstree-collapse-all").click(() => this.tree.jstree("close_all"));

            this._initJsTree();
        },

        _payload: function (extra) {
            const payload = $.extend({ id: this.options.resourceId }, extra);

            if (this.options.resourceViewId && this.options.resourceViewId !== true) {
                payload.view_id = this.options.resourceViewId;
            }

            return payload;
        },

        _moreNodeId: function (parentId) {
            return parentId + "::unfold-more";
        },

        /**
         * jstree `core.data` callback. Called once with the root ("#") and,
         * in lazy mode, again for every folder the user opens (or reloads
         * after "show more").
         */
        _loadNodes: function (node, callback) {
            this.loadState.show();

            const limit = this.folderLimits[node.id] || this.options.pageSize;

            $.ajax({
                url: this.sandbox.url("/api/action/get_archive_structure"),
                data: this._payload({ parent: node.id, limit: limit }),
            })
                .done((response) => {
                    const result = response.result;

                    if (result.error) {
                        this._displayErrorReason(result.error);
                        callback.call(this.tree.jstree(true), []);
                        return;
                    }

                    let nodes = result.nodes;

                    // Any exception here would leave jstree's own "Loading ..."
                    // placeholder in place forever, so surface it instead.
                    try {
                        if (node.id === "#") {
                            this.mode = result.mode;
                            this.total = result.total;
                            this._applyMode();
                        }

                        if (result.has_more) {
                            nodes.push(this._moreNode(node.id, nodes.length, result.children_total));
                        }
                    } catch (e) {
                        this._displayErrorReason(String(e));
                        nodes = [];
                    }

                    callback.call(this.tree.jstree(true), nodes);
                })
                .fail((xhr) => {
                    const message = xhr.status
                        ? ckan.i18n._("Could not load the archive listing") + " (HTTP " + xhr.status + ")"
                        : ckan.i18n._("Could not load the archive listing");
                    this._displayErrorReason(message);
                    callback.call(this.tree.jstree(true), []);
                })
                .always(() => this.loadState.hide());
        },

        _moreNode: function (parentId, shown, total) {
            const text = ckan.i18n._("Show more (%(shown)s of %(total)s shown)", {
                shown: shown.toLocaleString(),
                total: total.toLocaleString(),
            });

            return {
                id: this._moreNodeId(parentId),
                text: text,
                icon: "fa fa-ellipsis-h",
                li_attr: { class: "unfold-load-more" },
                a_attr: { tabindex: "0" },
                data: { load_more: true, parent: parentId },
                children: false,
            };
        },

        _loadMore: function (parentId) {
            const instance = this.tree.jstree(true);
            const current = this.folderLimits[parentId] || this.options.pageSize;

            this.folderLimits[parentId] = current + this.options.pageSize;

            // reloading the folder replaces its children in a single redraw
            instance.load_node(parentId, () => instance.open_node(parentId));
        },

        _applyMode: function () {
            const count = this.total.toLocaleString();

            if (this.mode === "lazy") {
                this.meta.text(ckan.i18n._("%(count)s entries, folders load when opened", { count: count }));
                // open_all would request every folder in the archive
                this.expandAll.prop("disabled", true)
                    .attr("title", ckan.i18n._("Not available for large archives"));
            } else {
                this.meta.text(ckan.i18n._("%(count)s entries", { count: count }));
            }
        },

        _search: function (query) {
            query = (query || "").trim();

            if (!query) {
                this._clearSearch();
                return;
            }

            if (this.mode !== "lazy") {
                this.tree.jstree("search", query);
                return;
            }

            // Large archive: matches may sit in folders that are not loaded
            // (or past their first page), so results are shown as a flat
            // list instead of highlighted in the tree.
            this.loadState.show();

            $.ajax({
                url: this.sandbox.url("/api/action/search_archive_structure"),
                data: this._payload({ q: query, limit: this.options.searchLimit }),
            })
                .done((response) => {
                    const result = response.result;

                    if (result.error) {
                        this._displayErrorReason(result.error);
                        return;
                    }

                    try {
                        let text = ckan.i18n._("%(count)s matches", { count: result.matches.toLocaleString() });

                        if (result.truncated) {
                            text += " " + ckan.i18n._("(showing the first %(limit)s)", { limit: this.options.searchLimit });
                        }

                        this.meta.text(text);
                        this._showResults(result.results);
                    } catch (e) {
                        this._displayErrorReason(String(e));
                    }
                })
                .fail(() => this._displayErrorReason(ckan.i18n._("Search failed")))
                .always(() => this.loadState.hide());
        },

        _showResults: function (rows) {
            const list = this.results.empty();

            if (!rows.length) {
                list.append($("<div>", { class: "unfold-result unfold-result--empty", text: ckan.i18n._("No entries match") }));
            }

            rows.forEach((row) => {
                // text() everywhere: names come from the archive and are untrusted
                const item = $("<div>", { class: "unfold-result" });
                $("<i>", { class: row.icon + " unfold-result-icon" }).appendTo(item);
                $("<span>", { class: "unfold-result-path", text: row.id, title: row.id }).appendTo(item);
                $("<span>", { class: "unfold-node-metadata" })
                    .append($("<span>", { class: "unfold-node-size", text: row.size }))
                    .append($("<span>", { class: "unfold-node-modified-at", text: row.modified_at }))
                    .appendTo(item);
                list.append(item);
            });

            this.tree.hide();
            list.show();
        },

        _clearSearch: function () {
            if (this.mode === "lazy") {
                this.results.hide().empty();
                this.tree.show();
            } else {
                this.tree.jstree("clear_search");
            }

            this._applyMode();
        },

        _setupKeyboardNavigation: function () {
            // Handle TAB, SHIFT+TAB navigation
            this.tree.on("keydown.jstree", ".jstree-anchor", (e) => {
                if (e.key === "Tab") {
                    e.preventDefault();
                    this._handleTabNavigation(e.shiftKey, $(e.currentTarget));
                }
            });
        },

        _handleTabNavigation: function (isShiftTab, currentAnchor) {
            // Get all visible anchors in the tree
            const allAnchors = this.tree.find(".jstree-anchor:visible");
            const currentIndex = allAnchors.index(currentAnchor);

            let targetIndex;
            if (isShiftTab) {
                // Move to previous anchor, or stay at first if already there
                targetIndex = currentIndex > 0 ? currentIndex - 1 : 0;
            } else {
                // Move to next anchor, or stay at last if already there
                targetIndex = currentIndex < allAnchors.length - 1 ? currentIndex + 1 : allAnchors.length - 1;
            }

            const targetAnchor = allAnchors.eq(targetIndex);
            targetAnchor.focus();
        },

        _displayErrorReason: function (error) {
            $("#archive-tree--loader").remove();
            $("#archive-tree-error span").text(error);
            $("#archive-tree-error").show();
        },

        _initJsTree: function () {
            let plugins = ["search", "wholerow"];

            if (this.options.showContextMenu) {
                plugins.push("contextmenu");
            }

            this.tree = $(this.el)
                .on("ready.jstree", () => {
                    $("#archive-tree--loader").remove();
                    this._setupKeyboardNavigation();

                    if (this.total < this.options.animationThreshold) {
                        this.tree.jstree(true).settings.core.animation = 200;
                    }
                })
                .on("activate_node.jstree", (_, data) => {
                    if (data.node.data && data.node.data.load_more) {
                        this._loadMore(data.node.data.parent);
                        return;
                    }

                    this.tree.jstree("toggle_node", data.node);
                })
                .jstree({
                    core: {
                        data: this._loadNodes,
                        themes: { dots: false },
                        // animation is decided once the size is known
                        animation: 0,
                        multiple: false,
                        // nodes are sorted on the server; no sort plugin needed
                    },
                    search: {
                        show_only_matches: this.options.searchShowOnlyMatches,
                        close_opened_onclear: this.options.searchCloseOpenedOnClear,
                        search_callback: (str, node) => {
                            const query = str.toLowerCase();
                            return (
                                node.id.toLowerCase().includes(query) ||
                                node.data?.size?.toLowerCase().includes(query) ||
                                node.data?.modified_at?.toLowerCase().includes(query)
                            );
                        },
                    },
                    contextmenu: {
                        items: this._getContextMenuItems,
                    },
                    plugins: plugins,
                });

            if (!this.options.showContextMenu) {
                this.tree.on("select_node.jstree", (_, data) => {
                    const node = data.node;
                    const nodeHref = node.a_attr?.href || null;
                    const nodeTarget = node.a_attr?.target || "_self";

                    if (nodeHref && nodeHref !== "#") {
                        window.open(nodeHref, nodeTarget);
                    }
                });
            }
        },

        _getContextMenuItems: function (node) {
            const items = {};
            const nodeHref = node.a_attr?.href || null;

            if (node.data && node.data.load_more) {
                return false;
            }

            if (nodeHref && nodeHref !== "#") {
                items["openURL"] = {
                    label: ckan.i18n._("Open URL"),
                    action: () => {
                        window.open(nodeHref, "_blank");
                    },
                };

                items["copyURL"] = {
                    label: ckan.i18n._("Copy URL"),
                    action: () => {
                        navigator.clipboard.writeText(nodeHref);
                    },
                };
            }

            if (node.children.length > 0 || node.state.loaded === false) {
                items["toggle"] = {
                    label: node.state.opened ? ckan.i18n._("Collapse") : ckan.i18n._("Expand"),
                    action: () => {
                        if (node.state.opened) {
                            this.tree.jstree("close_node", node);
                        } else {
                            this.tree.jstree("open_node", node);
                        }
                    },
                };
            }

            if (!Object.keys(items).length) {
                return false;
            }

            return items;
        }
    };
});
