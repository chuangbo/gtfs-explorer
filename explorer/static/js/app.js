// TODO: refine or re-write this ugly script or split it to modules using require.js
// TODO: consider if it's necessary to use Backbone here. Maybe just a router.js?
// FIXME: drop dependency of Backbone.Leaflet, it has many bug and hard to find out

/* Single-Page-App, using Backbone, Leaflet and Backbone.Leaflet 3rd-party extension
  Backbone.Router to manage url
  Backbone.Leaflet to manage Leaflet's `layer` as a Backbone Collection
 */

// Avoid `console` errors in browsers that lack a console.
(function() {
    var method;
    var noop = function () {};
    var methods = [
        'assert', 'clear', 'count', 'debug', 'dir', 'dirxml', 'error',
        'exception', 'group', 'groupCollapsed', 'groupEnd', 'info', 'log',
        'markTimeline', 'profile', 'profileEnd', 'table', 'time', 'timeEnd',
        'timeStamp', 'trace', 'warn'
    ];
    var length = methods.length;
    var console = (window.console = window.console || {});

    while (length--) {
        method = methods[length];

        // Only stub undefined methods.
        if (!console[method]) {
            console[method] = noop;
        }
    }
}());

(function (Backbone, _, L) {
  'use strict';

  var Features = Backbone.Leaflet.GeoCollection.extend({
    url: '/features.geojson'
  });

  var StopInfoPopupView = Backbone.View.extend({
    // Backbone.Leaflet.PopupView not design for this app,
    // we need a popup do not bind on one stop model
    // so that the popup would not disappear when stops reset.
    // And when first time viewing the page with stop router,
    // popup info maybe be loaded before stops, this is another
    // reason not bind popup in a model.
    template: _.template($('#stop-popup-template').html()),
    model: new Backbone.Model,

    initialize: function () {
      this.popup = L.popup();
      // when model change, popup will re-render itself.
      this.listenTo(this.model, "change", this.render);
    },

    render: function () {
      if (this.popup._content !== this.el) {
        this.popup.setContent(this.el);
      }
      this.$el.html(this.template(this.model.toJSON()));
      this.popup.setLatLng(this.model.get('point').reverse());
      return this;
    }
  });

  // A model contains bounds and zoom, useful for listen to map changing
  var BoundsModel = Backbone.Model.extend({
    defaults: {
      lat: '',
      lng: '',
      zoom: 15
    }
  });

  // A Leaflet control to close the route view, exit to stops view
  var RouterCloseBtnView = Backbone.View.extend({
    template: _.template($('#route-close-template').html()),

    initialize: function () {
      this.listenTo(this.model, "change", this.render);

      this.btn = L.control();

      var $this = this;

      this.btn.onAdd = function (map) {
        return $this.el;
      };
    },

    render: function () {
      // change the link
      this.$el.html(this.template(this.model.attributes));

      if (this.model.get('active')) {
        this.$el.show();
      } else {
        this.$el.hide();
      }
    }
  });

  // Extend `Backbone.Leaflet.MapView` to bind map events.
  var MapView = Backbone.Leaflet.MapView.extend({
    // Bind `map` events using `map` as selector.
    events: {
      'moveend map': 'onMove',
      'click map': 'onMapClick',
      'click layer': 'onLayerClick',
      'add layer': 'fitRouteBounds'
    },

    route_popup_template: _.template($('#route-popup-template').html()),

    initialize: function () {
      this._ensureMap();
      this.stopPopup = new StopInfoPopupView();
      this.view_type = 'stops';
      this.close_route_bounds_model = new BoundsModel();
      this.close_btn_view = new RouterCloseBtnView({model: this.close_route_bounds_model});
      this.close_btn_view.btn.addTo(this.map);

      // nprogress
      this.listenTo(this.collection, 'request', NProgress.start);
      this.listenTo(this.collection, 'reset', NProgress.done);
    },

    // set Url to current view
    onMove: function (e) {
      // reload stops on stops view
      if (this.view_type == 'stops') {
        this._load_stops();
      }

      // update url
      var new_route;
      if (!/@/.test(window.location.pathname)) {
        new_route = window.location.pathname + '/' + this._getRouteBoundsStr();
      } else {
        new_route = window.location.pathname.replace(/@.*$/, this._getRouteBoundsStr());
      }
      // replace the route without trigger the router.
      this.router.navigate(new_route, {replace: true});
      // send to Google Analytics
      this.router.trackPageview();
      // update bounds model
      this.close_route_bounds_model.set(this._getRouteBounds());
    },

    stopsView: function (lat, lng, zoom) {
      this.view_type = 'stops';
      this._load_stops();
      this.close_route_bounds_model.set('active', false);
      this.map.setView([lat, lng], zoom);
    },

    // close stop popup when click the map
    onMapClick: function (map) {
      if (this.view_type == 'stops') {
        this.router.navigate(this._getRouteBoundsStr());
        this.router.trackPageview();
      }
    },

    // Open the popup window on click.
    onLayerClick: function (e) {
      var layer = e.target;
      var model = this.collection.get(layer);

      if (model.get('stop_id')) {
        // navigate to stop view
        var code = model.get('code');
        // Just trigger the router, and the router will display proper view.
        this.router.navigate('/stop/' + code + '/' + this._getRouteBoundsStr(), {trigger: true});

      } else if (model.get('route_id')) {
        // open route popup directly, because when route view,
        // we don't reload and reset the collection, so that the popup
        // will not be remove when drag & move the map view
        layer.bindPopup(this.route_popup_template(model.toJSON())).openPopup();
      }
    },

    // Display a popup on a `stop`.
    stopView: function (stop_code, lat, lng, zoom) {
      var $this = this;
      this.map.setView([lat, lng], zoom);

      // load the `stop` information for routes data
      // add progress bar
      NProgress.start();
      $.ajax({
        url: '/stop_routes.json',
        action: 'get',
        data: {stop_code: stop_code}
      }).success(function (json) {
        // progress bar end
        NProgress.done();
        $this.stopPopup.model.set(json);
        $this.stopPopup.popup.openOn($this.map);
      });
    },

    // Display a `route` and the `stops` it pass through on the map.
    // and do not reload the collection on this view.
    // Display a button to close this view.
    routeView: function (short_name, lat, lng, zoom) {
      if (lat && lng && zoom) {
        this.map.setView([lat, lng], zoom);
      }
      this.view_type = 'route';
      this.route_short_name = short_name;
      this.close_route_bounds_model.set('active', true);
      this._load_route();
    },

    // Automatic fit the map view to one route. Every time the map draw a route
    // on it, this function will auto fit the view. THIS MIGHT BE A BUG! FIXME
    fitRouteBounds: function (e) {
      // only do this on `route` view
      if (this.view_type != 'route') {
        return;
      }
      var layer = e.target;
      var model = this.collection.get(layer);
      // find the first route and auto pan to it
      if (model.get('route_id')) {
        this.map.fitBounds(layer.getBounds());
      }
    },

    // Actually load and display the stops in map when user move the map.
    _load_stops: function () {
      var zoom = this.map.getZoom();
      var bounds = this.map.getBounds();
      var sw = bounds.getSouthWest();
      var ne = bounds.getNorthEast();

      this.collection.fetch({
        data: {
          type: 'stops',
          bounds: sw.lat + ',' + sw.lng + ',' + ne.lat + ',' + ne.lng,
          zoom: zoom
        },
        // trigger reset event to force Backbone.Leaflet parse geojson
        reset: true
      });
    },

    _load_route: function () {
      this.collection.fetch({
        data: {
          type: 'route',
          route_short_name: this.route_short_name
        },
        // trigger reset event to force Backbone.Leaflet parse geojson
        reset: true
      });
    },

    // return a object contains latlng and zoom info of current map view
    _getRouteBounds: function () {
      var point = this.map.getCenter();
      var zoom = this.map.getZoom();

      return {
        lat: point.lat.toFixed(7),
        lng: point.lng.toFixed(7),
        zoom: zoom
      };
    },

    // return a string for router contains latlng and zoom info of current map view
    _getRouteBoundsStr: function () {
      var b = this._getRouteBounds();
      return '@' + b.lat + ',' + b.lng + ',' + b.zoom;
    },

    // Override the method used the set the layer style to display different size of icon.
    // Size of icon should be bigger when zoom-in.
    layerStyle: function (model) {
      var zoom = this.map.getZoom();
      var size =
        zoom < 15 ? 10 :
          zoom < 16 ? 12 :
            zoom < 17 ? 14 :
              zoom < 18 ? 16 : 20;

      return {
        icon: L.icon({
          iconUrl: '/static/img/NPS_bus_stop.svg',
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
          popupAnchor: [0, -(size / 2) - 5]
        }),
        title: '(' + model.get('code') + ') ' + model.get('name'),
        riseOnHover: true
      }
    }
  });


  var WorkspaceRouter = Backbone.Router.extend({

    routes: {
      // redirect to Auckland Central as default map view
      "": "redirect",
      // naked map without any popup
      "@:lat,:lng,:zoom": "naked_map",
      // with a stop info popup
      "stop/:stop_code/@:lat,:lng,:zoom": "stop_view",
      // show one route and stops on it
      "route/:route_short_name": "route_view",
      "route/:route_short_name/@:lat,:lng,:zoom": "route_view"
    },

    initialize: function () {
      // create instances of views

      // create map view
      this.map = new MapView({
        el: "#map",
        collection: new Features,
        // leaflet map options
        map: {
          // set default view to Auckland Central, cause we only support just
          // one city right now.
          center: [-36.849285, 174.7671101],
          zoom: 15
        }
      });
      this.map.router = this;

      //track every route change as a page view in google analytics
      this.bind('route', this.trackPageview);
    },

    redirect: function () {
      // set viewport to Auckland Central
      this.navigate('@-36.849285,174.7671101,15', {trigger: true, replace: true})
    },

    naked_map: function (lat, lng, zoom) {
      this.map.stopsView(lat, lng, zoom);
    },

    stop_view: function (stop_code, lat, lng, zoom) {
      this.map.stopView(stop_code, lat, lng, zoom);
    },

    route_view: function (route_short_name, lat, lng, zoom) {
      this.map.routeView(route_short_name, lat, lng, zoom);
    },

    trackPageview: function () {
      var url = Backbone.history.getFragment();

      //prepend slash
      if (!/^\//.test(url) && url != "") {
        url = "/" + url;
      }

      if (_.isFunction(window.ga)) {
        ga('send', 'pageview', url);
      }
    }

  });

  $(function () {
    // start router, start rock
    var router = new WorkspaceRouter();
    Backbone.history.start({pushState: true});

    // do not reload when click a router link, use backbone's way instead.
    $(document).on('click', '[data-toggle="route"]', function (e) {
      e.preventDefault();
      router.navigate($(e.target).attr('href'), {trigger: true});
    });

    console.log("Hi, welcome! Nice to meet you! I am @chuangbo and available "
      + "for hire! Contact me directly via im@chuangbo.li!")
  });

})(Backbone, _, L);
