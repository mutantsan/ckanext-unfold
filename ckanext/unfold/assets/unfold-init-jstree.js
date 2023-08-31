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
                'core': {
                    'data': this.options.data
                },
                "plugins": [
                    "search"
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
