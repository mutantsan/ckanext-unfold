ckan.module("unfold-init-jstree", function ($, _) {
    "use strict";
    return {
        options: {
            data: null,
        },

        initialize: function () {
            $.proxyAll(this, /_on/);

            this.tree = $(this.el)

            $("#jstree-search").on("change", this._onSearch);
            $("#jstree-search-clear").click(this._onClearSearch);

            $(this.el).jstree({
                core: {
                    data: this.options.data,
                    themes: {
                        dots: false
                    }
                },
                search: {
                    show_only_matches: true,
                },
                table: {
                    columns: [
                        {width: 400, header: "Name"},
                        {width: 100, header: "Size", value: "size"},
                        {width: 100, header: "Type", value: "type"},
                        {width: 100, header: "Format", value: "format"},
                        {width: 100, header: "Modified at", value: "modified_at"}
                    ],
                    resizable: true,
                    height: 700
                },
                plugins: [
                    "search", "table", "sort"
                ]
            });
        },

        _onSearch: function (e) {
            this.tree.jstree("search", $(e.target).val())
        },

        _onClearSearch: function (e) {
            $("#jstree-search").val("").trigger("change");
        }
    };
});
