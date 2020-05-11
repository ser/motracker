/*
 * Main Javascript file for motracker.
 *
 * This file bundles all of your javascript together using webpack.
 */

// JavaScript modules
require('@fortawesome/fontawesome-free');
require('jquery');
require('moment');
require('popper.js');
require('bootstrap');
require('bricklayer');
require('leaflet');
require('leaflet-extra-markers');
require('leaflet-ajax');
require('leaflet-realtime');

// Your own code
require('./plugins.js');
require('./script.js');
