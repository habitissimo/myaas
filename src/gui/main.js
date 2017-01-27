$(function(){

  $(".ui.checkbox").checkbox();
  $("select.dropdown").dropdown();

  var TemplateModel = Backbone.Model.extend({
    parse: function(response) {
      return {
        name: response
      }
    },
  });

  var urls = {
    templates: '/v1/templates',
    db: '/v1/db',
  }

  var TemplateCollection = Backbone.Collection.extend({
    url: urls.templates,
    model: TemplateModel,
    parse: function(response) {
      return response.templates;
    },
  });

  var templates = new TemplateCollection;

  var DatabaseModel = Backbone.Model.extend({
    validate: function(attrs, options) {
      if( !_.has(attrs, "template") ) {
        return "Template attr must be set";
      }
      if( !_.has(attrs, "name") ) {
        return "name attr must be set";
      }
      if(attrs.name.length <= 1) {
        return "Database name too short (1)";
      }
      var template_names = templates.map(e => e.get("name"));
      if(!_.contains(template_names, attrs.template)) {
        return "Not a valid template";
      }
    },
    parse: function(response, options) {
      response.id = response.name;
      return response;
    },
    sync: function(method, model, options) {
      var attrs = model.toJSON();
      var full_url = urls.db + "/" + attrs.template + "/" + attrs.name;
      var model_context = model;
      if (method == 'create' || method == 'delete' || method == 'read') {
        options.url = full_url;
      }
      if (method == 'create') {
        var original_success_callback = options.success;
        options.success = function(model, body, response) {
          if (response.status == 304) {
            options.error("Database already exists");
          } else {
            original_success_callback(model, body, response);
          }
        }
      }
      //DatabaseModel.__super__.sync.call(this, method, model, options);
      Backbone.sync(method, model, options);
    },
    padLeft: function(number, length) {
      var number_str = number.toString();
      var final_str = number_str;
      while(final_str.length < length) {
        final_str = '0' + final_str;
      }
      return final_str;
    },
    formatDate: function(timestamp) {
      var date = new Date(timestamp * 1000);
      var year =  date.getFullYear();
      var day = date.getDate();
      var month = date.getMonth() + 1;
      var minutes = this.padLeft(date.getMinutes(), 2);
      var hours = this.padLeft(date.getHours(), 2);
      var date_part = year + "/" + month + "/" + day;
      var hour_part = hours + ":" + minutes;
      return date_part + " - " + hour_part;
    },
    formatedCreated: function(){
      return this.formatDate(this.get('created'))
    },
    formatedExpiresOn: function(){
      return this.formatDate(this.get('expires_at'))
    },
  });

  var DatabaseCollection = Backbone.Collection.extend({
    model: DatabaseModel,
    url: urls.db,
    parse: function(response) {
      return response.databases;
    },
  });

  var databases = new DatabaseCollection;

  var DatabaseView = Backbone.View.extend({
    template: _.template($("#db-row-template").html()),

    tagName: 'tr',

    events: {
      "click .delete": "deleteButtonClicked",
      "click .inspect": "inspectButtonClicked"
    },

    initialize: function() {
      this.listenTo(this.model, 'change', this.render);
    },

    render: function() {
      this.$el.html(this.template({model: this.model}));
      return this;
    },

    inspectButtonClicked: function(e) {
      var context = this;
      var button = $(e.target);
      button.prop('disabled', true);
      button.addClass('loading')
      this.model.fetch({
        success: function(model, response, options) {
          var modal_template = _.template($("#db_inspect_modal_template").html());
          var modal = $(modal_template({data: model.pick('host', 'password', 'port', 'state')}));
          modal.modal('show');
          modal.find('a').on('click', (e) => e.preventDefault());
          console.log(modal.find('a'));
          new Clipboard(modal.find('a').map((i, e) => e));
          button.prop('disabled', false);
          button.removeClass('loading');
        },
      });
    },

    deleteButtonClicked: function(e) {
      var context = this;
      var button = $(e.target);
      button.addClass('loading');
      button.prop('disabled', true);
      $('#db_delete_modal').modal({
        onApprove: function() {
          context.model.destroy({
            success: function(model, response) {
              context.remove();
            }
          });
        },
        onDeny: function() {
          button.removeClass('loading');
          button.prop('disabled', false);
        },
        closable: false,
      }).modal('show');
    },
  });


  var ErrorMessageView = Backbone.View.extend({
    template: _.template($("#error-message-template").html()),
    tagName: 'div',
    className: 'ui hidden negative transition message',
    events: {
      'click .close.icon': 'closeClicked',
    },
    initialize: function(header, message) {
      this.data = {
        header: header,
        message: message,
      };
    },
    render: function() {
      this.$el.html(this.template(this.data));
      window.setTimeout(function(context) {
        context.$el.transition({
          animation: 'fade',
          onComplete: () => context.remove(),
        });
        //context.remove();
      }, 3000, this);
      return this;
    },
    closeClicked: function(e) {
      this.remove();
    },
  });

  var AppView = Backbone.View.extend({
    id: "app",
    el: $("#app"),
    databaseContainer: $('#databases-container'),
    dbTemplateSelectorTemplate: _.template($('#option-db-template').html()),
    databasesSelector: $('#databases-selector'),
    db_name_input: $("#database_name"),
    new_db_button: $("#new_db"),

    events: {
      'click #new_db': 'createDbClicked',
    },

    initialize: function() {
      this.listenTo(databases, 'add', this.addDatabase);
      this.listenTo(databases, 'reset', this.addAllDatabases);
      this.listenTo(templates, 'add', this.addDBTemplate);
      templates.fetch();
      databases.fetch();

      var now = new Date();
      var max = new Date(now.getTime() + 24 * 3600 * 1000); // In 24h

      this.ttl_calendar = $("#calendar").calendar({
        initialDate: now,
        minDate: new Date(now.getTime() + 3600000),
        maxDate: max,
        startMode: 'day',
        disableYear: true,
        disableMinute: true,
        firstDayOfWeek: 1,
        text: {
          days: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        }
      });
    },

    clearDbInput: function() {
      this.db_name_input.val('');
      this.ttl_calendar.find('input').val('');
    },

    createDbClicked: function() {
      var context = this;
      context.new_db_button.prop("disabled", true);
      context.new_db_button.addClass('loading');
      var now = new Date();
      var expire_date = new Date(context.ttl_calendar.find("input").val());
      var ttl = new Date((expire_date.getTime() / 1000) - (now.getTime() / 1000));
      var db = new DatabaseModel({
          name: context.db_name_input.val(),
          template: context.databasesSelector.val(),
          ttl: ttl.getTime(),
      });

      var exit = function() {
        context.new_db_button.prop("disabled", false);
        context.new_db_button.removeClass('loading');
        context.clearDbInput();
      }

      db.save({},
        {
          success: function(model, response, options) {
            databases.add(db);
            exit();
          },
          error: function(model, response, options) {
            // TODO: Show error message
            var form = $('#create_db_form');
            var err_message_view = new ErrorMessageView(
              "Error creating database!",
              response
            );
            var rendered = err_message_view.render();
            form.append(rendered.el);
            rendered.$el.transition({
              animation: 'fade',
              duration: '1s',
            });
            //alert(response);
            exit();
          },
        }
      );
  
      if (!db.isValid()) {
        alert(db.validationError);
        exit();
        return;
      }
    },

    addDatabase: function(db) {
      var dbView = new DatabaseView({model: db});
      this.databaseContainer.append(dbView.render().el);
    },

    addDBTemplate: function(model) {
      var rendered = this.dbTemplateSelectorTemplate(model.toJSON());
      this.databasesSelector.append(rendered);
    },

    addAllDatabases: function() {
      databases.each(this.addDatabase, this);
    },
  });

  var app = new AppView;
});
