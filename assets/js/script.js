// <3 Maps
var map;

function initmap() {
  var geotrack = $.ajax({
    url: '/gnss/json/12',
    dataType: 'json',
    success: console.log('Track data successfully loaded.'),
    error: function (xhr) {
      alert(xhr.statusText)
    }
  });
  $.when(geotrack).done(function() {
    map = new L.Map('gnssmap');

    // https://opentopomap.org/
    // var osmUrl='https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png';<Paste>

    // https://manage.thunderforest.com/dashboard
    var osmUrl='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
    var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 30});
    map.addLayer(osm);

    var tracklayer = L.geoJSON(geotrack.responseJSON, {
      style: function(feature) {
        return { color: 'blue', weight: 4 };
      }
    }).addTo(map);

    map.fitBounds(tracklayer.getBounds());
  });
}
initmap();
