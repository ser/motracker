// <3 Maps are in templates

    function initrealtime() {
        //// Markers
        // Moto
        L.Marker.mergeOptions({
            icon: L.ExtraMarkers.icon({
                icon: 'fa-motorcycle',
                markerColor: 'green-light',
                shape: 'square',
                prefix: 'fa'
            })
        });

        // loading geoJSON
        var map = L.map('gnssmap'),
            realtime = L.realtime(`/gnss/jsonp/one/${trackid}`, {
                interval: 30 * 1000
        }).addTo(map);

        // https://opentopomap.org/
        // var osmUrl='https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png';

        // https://manage.thunderforest.com/dashboard
        var osmUrl='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
        var osm = new L.tileLayer(osmUrl, {minZoom: 1, maxZoom: 30});
        L.tileLayer(osmUrl, {minZoom: 1, maxZoom: 30}).addTo(map);


        // resizing the window
        // https://gis.stackexchange.com/questions/62491/sizing-leaflet-map-inside-bootstrap
        $('#gnssmap').css("height", ($(window).height() - 150));
        $(window).on("resize", resize);
        resize();

        function resize(){
            $('#gnssmap').css("height", ($(window).height() - 150 ));
            $('.leaflet-control-attribution').hide();
        }

        realtime.on('update', function() {
            map.fitBounds(realtime.getBounds(), {maxZoom: 17});
            $('.leaflet-control-attribution').hide();
        });
    }

    function initmap() {
        var map;
        var geotrack = $.ajax({
            url: `/gnss/json/${trackid}`,
            dataType: 'json',
            success: console.log('Track data successfully loaded.'),
            error: function (xhr) {
            //  alert(xhr.statusText)
                console.log('Problems.');
            }
        });
        $.when(geotrack).done(function() {
            map = new L.Map('gnssmap');

            // https://opentopomap.org/
            // var osmUrl='https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png';

            // https://manage.thunderforest.com/dashboard
            var osmUrl='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
            var osm = new L.TileLayer(osmUrl, {minZoom: 1, maxZoom: 30});
            map.addLayer(osm);

            var tracklayer = L.geoJSON(geotrack.responseJSON, {
                style: function(feature) {
                    return { color: 'blue', weight: 4 };
                }
            }).addTo(map);

            // resizing the window
            // https://gis.stackexchange.com/questions/62491/sizing-leaflet-map-inside-bootstrap
            $('#gnssmap').css("height", ($(window).height() - 150));
            $(window).on("resize", resize);
            resize();
            function resize(){
                $('#gnssmap').css("height", ($(window).height() - 150 ));
                $('.leaflet-control-attribution').hide();
            }

            map.fitBounds(tracklayer.getBounds());
        });
    }
    if (typeof trackid !== 'undefined') {
        if (typeof realtime !== 'undefined') {
            initrealtime();
        }
        else {
            initmap();
        }
    }
var all = document.getElementsByTagName("svg");
for (var i=0, max=all.length; i < max; i++) {
var bbox = all[i].getBBox();

var viewBox;

if(bbox.width > bbox.height){
viewBox = [bbox.x, bbox.y - (bbox.width - bbox.height)/2, bbox.width, bbox.width].join(" ")
} else if (bbox.width < bbox.height){
viewBox = [bbox.x - (bbox.height - bbox.width)/2, bbox.y, bbox.height, bbox.height].join(" ")
} else {
viewBox - [bbox.x, bbox.y, bbox.width, bbox.height].join(" ");
}
all[i].setAttribute("viewBox", viewBox);
console.log(viewBox);
}

