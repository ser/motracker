// <3 Maps are in templates

    function initrealtime() {

            if (!window.WebSocket) {
                if (window.MozWebSocket) {
                    window.WebSocket = window.MozWebSocket;
                } else {
                    console.log("Your browser doesn't support WebSockets.");
                }
            }

            var ws = new WebSocket('wss://motracker.random.re/rt/' + trackrid);

            ws.onopen = function(evt) {
                console.log('WebSocket connection opened.');
            }

            ws.onmessage = function(evt) {
                // console.log(evt.data);
                if (evt.data == "UP") { realtime.update(); }
            }

            ws.onclose = function(evt) {
                console.log('WebSocket connection closed.');
            }

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

        // lastmarker.bindPopup("ALA").openPopup();

        // loading geoJSON
        var map = L.map('gnssmap');
        var realtime = L.realtime(`/gnss/jsonp/5/${trackrid}`, {
            start: false,
            onEachFeature: function (feature, layer) {
                var speed = "Speed: ";
                speed = speed + feature.properties.speed;
                //console.log(speed);
                altitude = "Altitude: ";
                altitude = altitude + feature.properties.altitude;
                var sat = "Sattelites: ";
                sat = sat + feature.properties.sat
                var popap = layer.bindPopup(speed+"\n"+altitude);
                console.log(feature.properties);
                $('#speed').html( speed );
                $('#altitude').html( altitude );
                $('#satt').html( sat );
                $('#name').html( feature.properties.comment );
                //var k =  moment( feature.properties.timez ).fromNow();
                //console.log(moment().format());
                $('#when').html( feature.properties.timez );
            }
        }).addTo(map);

        //var realine = L.geoJSON.AJAX('/gnss/json/${trackrid}/5').addTo(map);
        var realine = L.geoJson.ajax().addTo(map);
        realine.addUrl(`/gnss/json/${trackrid}/5`);

        // https://opentopomap.org/
        //var osmUrl='https://{a|b|c}.tile.opentopomap.org/{z}/{x}/{y}.png';

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
            realine.refresh();
        });
    }

    function initmap() {
        var map;
        var geotrack = $.ajax({
            url: `/gnss/json/${trackrid}/0`,
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
            //var osmUrl='https://tile.thunderforest.com/outdoors/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
            var osmUrl='https://tile.thunderforest.com/neighbourhood/{z}/{x}/{y}.png?apikey=4c4eaae4021441eea631ed97ed487943';
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
    if (typeof trackrid !== 'undefined') {
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
