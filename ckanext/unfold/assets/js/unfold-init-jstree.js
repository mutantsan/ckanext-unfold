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
            this.loader = $("#archive-tree--loader");
            this.errorBlock = $("#archive-tree-error");
            this.errorMessage = this.errorBlock.find(".unfold-error-message");
            this.retryButton = $("#archive-tree-retry");
            // re-runs the request whose failure is currently displayed
            this.retry = null;
            this.loadState = $(".unfold-load-state");
            this.meta = $(".unfold-tree-meta");
            this.expandAll = $("#jstree-expand-all");
            this.results = $("#archive-search-results");
            this.searchInput = $("#jstree-search");
            this.searchClear = $("#jstree-search-clear");
            // "full": every node is in the DOM; "lazy": folders load on open
            this.mode = null;
            this.total = 0;
            // lazy mode: how many children each folder currently shows
            this.folderLimits = {};

            this.searchInput.on("input", this._toggleSearchClear);
            this.searchInput.on("change", (e) => this._search($(e.target).val()));
            $("#jstree-search-run").click(() => this._search(this.searchInput.val()));
            this.searchClear.click(() => {
                this.searchInput.val("").trigger("focus");
                this._toggleSearchClear();
                this._clearSearch();
            });
            this.expandAll.click(() => this.tree.jstree("open_all"));
            $("#jstree-collapse-all").click(() => this.tree.jstree("close_all"));
            this.retryButton.click(() => {
                if (this.retry) {
                    this.retry();
                }
            });

            this._observeMetadata();
            this._initJsTree();
        },

        teardown: function () {
            if (this._metadataObserver) {
                this._metadataObserver.disconnect();
            }
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
            const instance = this.tree.jstree(true);

            this._clearError();
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
                        callback.call(instance, []);
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

                    callback.call(instance, nodes);
                })
                .fail((xhr) => {
                    if (node.id === "#") {
                        // An empty root lets jstree finish initialising and
                        // drop its own "Loading ..." row; refresh() re-runs
                        // this callback for the root.
                        callback.call(instance, []);
                        this._displayErrorReason(
                            this._requestFailure(ckan.i18n._("Could not load the archive listing"), xhr),
                            () => instance.refresh()
                        );
                        return;
                    }

                    // `false` leaves the folder unloaded, so opening it
                    // again requests it again.
                    callback.call(instance, false);
                    this._displayErrorReason(
                        this._requestFailure(ckan.i18n._("Could not load folder %(name)s", { name: node.id }), xhr),
                        () => instance.load_node(node.id, (loaded, ok) => ok && instance.open_node(loaded))
                    );
                })
                .always(() => this.loadState.hide());
        },

        _requestFailure: function (message, xhr) {
            return xhr.status ? message + " (HTTP " + xhr.status + ")" : message;
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
            instance.load_node(parentId, (node, ok) => ok && instance.open_node(node));
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
            this._clearError();
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
                .fail((xhr) => this._displayErrorReason(
                    this._requestFailure(ckan.i18n._("Search failed"), xhr),
                    () => this._search(query)
                ))
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

        _toggleSearchClear: function () {
            this.searchClear.toggle(this.searchInput.val().length > 0);
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

        /**
         * Show `error` above the tree. When `retry` is given a Retry button
         * is offered that calls it; API errors such as a wrong password
         * pass no retry because repeating the request cannot help.
         */
        _displayErrorReason: function (error, retry) {
            this.loader.hide();
            this.retry = retry || null;
            this.retryButton.toggle(!!retry);
            this.errorMessage.text(error);
            this.errorBlock.show();
        },

        _clearError: function () {
            this.retry = null;
            this.errorBlock.hide();
        },

        _initJsTree: function () {
            let plugins = ["search", "wholerow"];

            if (this.options.showContextMenu) {
                plugins.push("contextmenu");
            }

            this.tree = $(this.el)
                .on("ready.jstree", () => {
                    this.loader.hide();
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
                        force_text: true,
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

        /**
         * jstree redraws by emptying and rebuilding whichever part of the
         * tree changed (a folder opening, a page loading, a search
         * filtering), so there is no single reliable "node rendered" event
         * to hook. Watching the DOM directly catches every anchor jstree
         * ever adds, however it got there.
         */
        _observeMetadata: function () {
            this._metadataObserver = new MutationObserver((mutations) => {
                const instance = this.tree.jstree(true);

                if (!instance) {
                    return;
                }

                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((added) => {
                        if (added.nodeType !== Node.ELEMENT_NODE) {
                            return;
                        }

                        if (added.matches(".jstree-anchor")) {
                            this._decorateAnchor(added, instance);
                        }

                        added.querySelectorAll(".jstree-anchor").forEach((anchor) =>
                            this._decorateAnchor(anchor, instance)
                        );
                    });
                });
            });

            this._metadataObserver.observe(this.el[0], { childList: true, subtree: true });
        },

        /**
         * Append the size/modified-at spans jstree does not know about.
         * Built with textContent, never innerHTML: `data.size` and
         * `data.modified_at` come from the archive and are untrusted.
         */
        _decorateAnchor: function (anchor, instance) {
            if (anchor.dataset.unfoldDecorated) {
                return;
            }

            anchor.dataset.unfoldDecorated = "1";

            const li = anchor.closest(".jstree-node");
            const node = li && instance.get_node(li.id);
            const data = node && node.data;

            if (!data || (!data.size && !data.modified_at)) {
                return;
            }

            const meta = document.createElement("span");
            meta.className = "unfold-node-metadata";

            if (data.size) {
                const size = document.createElement("span");
                size.className = "unfold-node-size";
                size.textContent = data.size;
                meta.appendChild(size);
            }

            if (data.modified_at) {
                const modifiedAt = document.createElement("span");
                modifiedAt.className = "unfold-node-modified-at";
                modifiedAt.textContent = data.modified_at;
                meta.appendChild(modifiedAt);
            }

            anchor.appendChild(meta);
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
