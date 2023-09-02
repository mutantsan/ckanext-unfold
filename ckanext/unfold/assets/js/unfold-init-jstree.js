ckan.module("unfold-init-jstree", function ($, _) {
    "use strict";
    return {
        options: {
            data: null,
            resourceId: null,
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            this.tree = $(this.el)
            this.errorBlock = $("#archive-tree-error");

            $("#jstree-search").on("change", this._onSearch);
            $("#jstree-search-clear").click(this._onClearSearch);

            $.ajax({
                url: this.sandbox.url("/api/action/get_archive_structure"),
                data: { "id": this.options.resourceId },
                success: this._onSuccessRequest,
                error: function (xhr, status, error) {}
            });
        },

        _onSearch: function (e) {
            this.tree.jstree("search", $(e.target).val())
        },

        _onClearSearch: function (e) {
            $("#jstree-search").val("").trigger("change");
        },

        _preparePayload: function () {
            return { "id": this.options.resourceId };
        },

        _onErrorRequest: function (xhr, status, error) {
            let errMsg = xhr.responseJSON.error;

            $(this.el).jstree(true).settings.plugins = [];
            $(this.el).jstree(true).destroy();

            $("#archive-tree-error").text("Error: " + errMsg)
        },

        _onSuccessRequest: function (data) {
            if (data.result.error) {
                this._displayErrorReason(data.result.error);
            } else {
                this._initJsTree(data.result)
            }
        },

        _displayErrorReason: function (error) {
            $("#archive-tree-error").text("Error: " + error);
        },

        _initJsTree: function (data) {
            $(this.el).jstree({
                core: {
                    data: data,
                    themes: { dots: false }
                },
                search: {
                    show_only_matches: true,
                },
                table: {
                    columns: [
                        { width: 400, header: "Name" },
                        { width: 100, header: "Size", value: "size" },
                        { width: 100, header: "Type", value: "type" },
                        { width: 100, header: "Format", value: "format" },
                        { width: 100, header: "Modified at", value: "modified_at" }
                    ],
                    height: 700,
                },
                plugins: [
                    "search", "table", "sort"
                ]
            });
        }
    };
});
