// <3 Maps
var map;

function initmap() {
  map = new L.Map('gnssmap');

  // https://opentopomap.org/
  // var osmUrl='https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png';<Paste>

  // https://manage.thunderforest.com/dashboard
  var osmUrl='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
  var osm = new L.TileLayer(osmUrl, {minZoom: 5, maxZoom: 30});
  map.setView([10.78713, 106.71091], 6);
  map.addLayer(osm);
}
initmap();
