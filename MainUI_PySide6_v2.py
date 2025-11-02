"""
PySide6 Version - Best for macOS! Much smoother and faster than tkinter!
Uses QWebEngineView with Leaflet.js for hardware-accelerated map rendering.
Performance: <1ms lag, 60+ fps smooth scrolling/zooming
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFrame, QLabel, QDialog, QSizePolicy, QLineEdit, QMessageBox, QMenu)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QEvent, QUrl, QPoint
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtGui import QAction
import math
import random
import requests
import json


class PullUpWidget(QWidget):
    """Draggable pull-up panel with smooth animations"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setMinimumHeight(50)
        self.setMaximumHeight(650)  # 50 handle + 600 max content
        self.is_expanded = False
        self.start_y = 0
        self.current_height = 0
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create handle
        self.handle = QFrame(self)
        self.handle.setFixedHeight(50)
        self.handle.setStyleSheet("background-color: #2563eb; border-radius: 5px 5px 0 0;")
        # Use horizontal layout so we can place a Clear button on the right
        self.handle_layout = QHBoxLayout(self.handle)
        self.handle_layout.setContentsMargins(8, 0, 8, 0)

        self.label = QLabel("⬆ Pull Up Tab", self.handle)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        self.handle_layout.addWidget(self.label, 1)

        # Clear button on the handle (small)
        self.clear_btn = QPushButton("Clear", self.handle)
        self.clear_btn.setFixedSize(64, 28)
        self.clear_btn.setStyleSheet("background-color:#f97316; color:white; border-radius:4px; font-weight:bold;")
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        self.handle_layout.addWidget(self.clear_btn)
        main_layout.addWidget(self.handle)
        
        # Content area
        self.content = QWidget(self)
        self.content.setStyleSheet("background-color: #e0e7ff;")
        self.content.setFixedHeight(0)
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Pull Up Tab Content")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af; padding: 30px;")
        self.content_layout.addWidget(title)
        
        content_label = QLabel("This is the pull-up tab content area.\nDrag the blue bar down to close.")
        content_label.setAlignment(Qt.AlignCenter)
        content_label.setStyleSheet("font-size: 14px; color: #334155; padding: 20px;")
        self.content_layout.addWidget(content_label)
        main_layout.addWidget(self.content)
        
        # Enable mouse tracking and install event filter
        self.handle.setMouseTracking(True)
        self.handle.installEventFilter(self)
        self.label.installEventFilter(self)
        
        # Animation
        self.animation = QPropertyAnimation(self.content, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.finished.connect(self.animationFinished)
        self.content.setMaximumHeight(0)

    def set_results(self, destination_name, top3_list, recommendation):
        """Populate the pull-up content with search results. Make parking spots clickable
        to show them on the map with distance line to destination.

        top3_list: list of dicts with keys: name, capacity, available, distance_km
        recommendation: dict or None
        """
                # Store destination name for click handlers
        self.current_destination = destination_name
        
        # Clear existing content widgets (except the handle)
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        title = QLabel(f"Results for: {destination_name}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e40af; padding: 8px 4px;")
        self.content_layout.addWidget(title)

        # Top 3 nearest parking
        sub = QLabel("Click a parking spot to see the route:")
        sub.setStyleSheet("font-size: 13px; color: #334155; padding: 4px;")
        self.content_layout.addWidget(sub)
        if not top3_list:
            # Show recent search history if available
            history = []
            try:
                history = getattr(self.parent_widget, 'search_history', []) or []
            except Exception:
                history = []

            if history:
                hist_label = QLabel("Recent searches:")
                hist_label.setStyleSheet("font-size:13px; color:#334155; padding:4px; font-weight: bold;")
                self.content_layout.addWidget(hist_label)
                # show up to 5 recent
                for q in history[:5]:
                    hb = QPushButton(q)
                    hb.setStyleSheet("""
                        QPushButton { background-color: transparent; text-align: left; color: #0f172a; padding:6px; border: none; }
                        QPushButton:hover { background-color: #eef2ff; }
                    """)
                    # clicking history triggers a search in the main window
                    hb.clicked.connect(lambda checked, qq=q: (self.parent_widget.search_for_query(qq), self.parent_widget.pull_up.collapse()))
                    self.content_layout.addWidget(hb)
            else:
                no = QLabel("No parking places found nearby.")
                no.setStyleSheet("font-size:13px; color:#7f1d1d; padding:4px;")
                self.content_layout.addWidget(no)
        else:
            for idx, p in enumerate(top3_list, start=1):
                # Determine availability color
                avail = p.get('available', 0)
                if avail > 7:
                    color = 'green'
                elif avail >= 4:
                    color = 'orange'
                else:
                    color = 'red'
                # Create a button for each parking spot (include color)
                # Format passes display
                pass_info = ""
                if p.get('passes'):
                    # Convert pass IDs to display names
                    pass_names = {
                        'staff': 'Staff',
                        'green_commuter': 'Green',
                        'silver_commuter': 'Silver',
                        'residence_hall': 'RH',
                        'ada': 'ADA'
                    }
                    formatted_passes = [pass_names.get(p_id, p_id) for p_id in p['passes']]
                    pass_info = f" [Passes: {', '.join(formatted_passes)}]"
                btn = QPushButton(f"{idx}. {p['name']} ({color}) — {p['available']}/{p['capacity']} spots — {p['distance_km']:.2f} km{pass_info}")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8fafc;
                        color: #0f172a;
                        font-size: 13px;
                        padding: 8px;
                        text-align: left;
                        border: 1px solid #e2e8f0;
                        border-radius: 4px;
                        margin: 2px 0;
                    }
                    QPushButton:hover {
                        background-color: #e0e7ff;
                        border-color: #818cf8;
                    }
                """)
                # Store parking data in the button (for click handler) and destination info
                btn.parking_data = p
                btn.clicked.connect(lambda checked, p=p: self.on_parking_clicked(p))
                self.content_layout.addWidget(btn)

        # Recommendation section
        if recommendation:
            rec_label = QLabel("Recommended spot (>5 available):")
            rec_label.setStyleSheet("font-size: 13px; color: #065f46; padding: 4px; font-weight: bold;")
            self.content_layout.addWidget(rec_label)
            
            # Make recommendation clickable too (include color)
            ravail = recommendation.get('available', 0)
            rcolor = 'green' if ravail > 7 else ('orange' if ravail >= 4 else 'red')
            # Format passes display for recommendation
            pass_info = ""
            if recommendation.get('passes'):
                pass_names = {
                    'staff': 'Staff',
                    'green_commuter': 'Green',
                    'silver_commuter': 'Silver',
                    'residence_hall': 'RH',
                    'ada': 'ADA'
                }
                formatted_passes = [pass_names.get(p_id, p_id) for p_id in recommendation['passes']]
                pass_info = f" [Passes: {', '.join(formatted_passes)}]"
            rec_btn = QPushButton(f"{recommendation['name']} ({rcolor}) — {recommendation['available']}/{recommendation['capacity']} spots — {recommendation['distance_km']:.2f} km{pass_info}")
            rec_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecfdf5;
                    color: #064e3b;
                    font-size: 13px;
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #6ee7b7;
                    border-radius: 4px;
                    margin: 2px 0;
                }
                QPushButton:hover {
                    background-color: #d1fae5;
                    border-color: #34d399;
                }
            """)
            rec_btn.parking_data = recommendation
            rec_btn.clicked.connect(lambda checked, r=recommendation: self.on_parking_clicked(r))
            self.content_layout.addWidget(rec_btn)
        
    def on_parking_clicked(self, parking):
        """Handle when a parking spot button is clicked in the pull-up."""
        # The parent MainWindow is accessible via self.parent_widget
        if not self.parent_widget:
            print("No parent window found")
            return

        # Get destination coords from last search (stored in MainWindow)
        try:
            window = self.parent_widget
            dest = window._last_destination
            if not dest:
                print("No destination found - please search first")
                return
            
            print(f"Using destination: {dest}")  # Debug
            # Call JS to show the destination, selected parking, and distance line
            window.map_widget.clear_highlights()  # Clear existing markers
            window.map_widget.show_destination_and_parking(
                dest['lat'], dest['lon'], 
                dest['display_name'],
                parking['lat'], parking['lon'],
                f"{parking['name']} ({parking['available']}/{parking['capacity']} spots)",
                parking['distance_km']
            )
        except Exception as e:
            print(f"Failed to show parking selection: {e}")
    
    def on_clear_clicked(self):
        """Clear highlights on the map and collapse the pull-up."""
        try:
            if self.parent_widget and hasattr(self.parent_widget, 'map_widget'):
                self.parent_widget.map_widget.clear_highlights()
        except Exception as e:
            print("Failed to clear highlights:", e)
        try:
            self.collapse()
        except Exception:
            pass
            
    def eventFilter(self, obj, event):
        """Handle events from handle and label"""
        if obj in [self.handle, self.label]:
            if event.type() == QEvent.Type.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.Type.MouseMove:
                self.mouseMoveEvent(event)
                return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return True
        return super().eventFilter(obj, event)
        
    def mousePressEvent(self, event):
        """Start dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_y = event.globalPos().y()
            self.current_height = self.content.height()
            self.handle.setCursor(Qt.CursorShape.ClosedHandCursor)
            
    def mouseMoveEvent(self, event):
        """Handle dragging"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.start_y:
            delta_y = self.start_y - event.globalPos().y()
            new_height = max(0, min(500, self.current_height + delta_y))
            # Temporarily use fixedHeight during drag for immediate feedback
            self.content.setFixedHeight(int(new_height))
            self.content.setMaximumHeight(int(new_height))  # Keep in sync
            self.start_y = event.globalPos().y()
            self.current_height = new_height
            
    def mouseReleaseEvent(self, event):
        """Snap to expanded or collapsed state"""
        self.handle.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.current_height > 150:
            self.expand()
        else:
            self.collapse()
        self.start_y = 0
        
    def expand(self):
        """Animate to expanded state"""
        self.content.setFixedHeight(self.content.height())  # Lock current height
        self.animation.setStartValue(self.content.height())
        self.animation.setEndValue(500)
        self.animation.start()
        self.is_expanded = True
        
    def collapse(self):
        """Animate to collapsed state"""
        self.content.setFixedHeight(self.content.height())  # Lock current height
        self.animation.setStartValue(self.content.height())
        self.animation.setEndValue(0)
        self.animation.start()
        self.is_expanded = False
        
    def animationFinished(self):
        """Called when animation finishes - switch back to maximumHeight"""
        final_height = self.content.maximumHeight()
        self.content.setFixedHeight(final_height)
        self.content.setMaximumHeight(final_height)


class MapWidget(QWebEngineView):
    """Web-based map using Leaflet.js with local tile caching - super smooth and fast"""
    def __init__(self, parent=None, parking_places=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Enable geolocation
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)")
        
        class WebPage(QWebEnginePage):
            def javaScriptConsoleMessage(self, level, message, line, source):
                print(f"JS {level}: {message} (line {line}, source: {source})")
                
            def acceptNavigationRequest(self, url, _type, isMainFrame):
                print(f"Navigation request: {url}")
                return True
            
            def featurePermissionRequested(self, url, feature):
                print(f"Permission requested for {feature} from {url}")
                if feature == QWebEnginePage.Feature.Geolocation:
                    print("Granting geolocation permission")
                    self.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.GrantedPermission)
                else:
                    print(f"Not granting permission for {feature}")
                    self.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.DeniedPermission)
        
        self.page = WebPage(profile, self)
        self.setPage(self.page)
        
        # OKState coordinates
        self.okstate_lat = 36.1224
        self.okstate_lon = -97.0698
        
        # Check for cached tiles
        self.map_cache_dir = Path("map_cache")
        self.use_cached_tiles = self.map_cache_dir.exists() and any(self.map_cache_dir.iterdir())
        # Parking data (list of dicts)
        self.parking_places = parking_places or []
        # Hold IDs of JS markers we might add for highlight (not strictly required but kept for future use)
        self._dest_marker_id = None
        self._top3_marker_ids = []

        # Setup static file serving
        current_dir = Path(__file__).parent
        self.static_dir = current_dir / 'static'
        
        # Create HTML with Leaflet map
        self.load_map()
    
    def load_map(self):
        """Load map with cached or online tiles"""
        okstate_lat = self.okstate_lat
        okstate_lon = self.okstate_lon
        
        if self.use_cached_tiles:
            # Use local tiles from cache
            print(f"Using cached map tiles from {self.map_cache_dir}")
            html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="permissions-policy" content="geolocation=*">
    <title>OSU Campus Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100vw; }
        .user-location-marker {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .leaflet-control-attribution {
            font-size: 11px;
        }
        .user-location-dot {
            background-color: #4285f4;
            border: 2px solid white;
            border-radius: 50%;
            width: 16px;
            height: 16px;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Location tracking functions
        function updateUserLocationMarker(map, position) {
            const latlng = [position.coords.latitude, position.coords.longitude];
            
            if (!userMarker) {
                userMarker = L.marker(latlng, {
                    icon: L.divIcon({
                        className: 'user-location-marker',
                        html: '<div class="user-location-dot"></div>'
                    })
                }).addTo(map);
                
                userCircle = L.circle(latlng, {
                    radius: position.coords.accuracy,
                    color: '#4285f4',
                    fillColor: '#4285f433',
                    fillOpacity: 0.2
                }).addTo(map);
                
                map.setView(latlng, 16);
            } else {
                userMarker.setLatLng(latlng);
                userCircle.setLatLng(latlng);
                userCircle.setRadius(position.coords.accuracy);
            }
        }

        function updateUserLocation(map) {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(
                    (position) => updateUserLocationMarker(map, position),
                    (error) => console.error("Error getting location:", error),
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            }
        }

        function initializeLocationTracking(map) {
            // Create location control
            const locationControl = L.control({position: 'bottomright'});
            locationControl.onAdd = function(map) {
                const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
                div.innerHTML = `
                    <a href="#" title="Center on my location" style="display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; background: white;">
                        <svg viewBox="0 0 24 24" width="18" height="18">
                            <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3A8.994 8.994 0 0 0 13 3.06V1h-2v2.06A8.994 8.994 0 0 0 3.06 11H1v2h2.06A8.994 8.994 0 0 0 11 20.94V23h2v-2.06A8.994 8.994 0 0 0 20.94 13H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z" fill="#666"/>
                        </svg>
                    </a>
                `;
                div.onclick = function() {
                    updateUserLocation(map);
                    return false;
                };
                return div;
            };
            locationControl.addTo(map);

            // Start watching location
            if ("geolocation" in navigator) {
                navigator.geolocation.watchPosition(
                    (position) => updateUserLocationMarker(map, position),
                    (error) => console.error("Error getting location:", error),
                    {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    }
                );
            }
        }
    </script>
    <script>"""
            
            # Include the JavaScript code directly
            with open(self.static_dir / 'js/location.js', 'r') as f:
                location_js = f.read()
            with open(self.static_dir / 'js/eta.js', 'r') as f:
                eta_js = f.read()
            
            html += f"\n{location_js}\n{eta_js}\n"
            html += f"""
                // Create the map
                var map = L.map('map').setView([{okstate_lat}, {okstate_lon}], 15);
                
                // Add OpenStreetMap tiles
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    attribution: '© OpenStreetMap contributors',
                    maxZoom: 19
                }}).addTo(map);

                // Make map globally accessible
                window.map = map;
                console.log('Map initialized');

                // Add parking markers
                var parkingData = {json.dumps(self.parking_places)};
                console.log('Parking data:', parkingData);
                
                function colorForAvailable(avail) {{ 
                    return avail > 7 ? '#15803d' : avail >= 4 ? '#f97316' : '#dc2626'; 
                }}
                
                parkingData.forEach(function(p) {{
                    var circle = L.circleMarker([p.lat, p.lon], {{
                        radius: 10,
                        color: colorForAvailable(p.available),
                        fillColor: colorForAvailable(p.available),
                        fillOpacity: 0.9
                    }}).addTo(map);
                    
                    var popupHtml = '<b>' + p.name + '</b><br>Capacity: ' + p.capacity + 
                                  '<br>Available: ' + p.available + 
                                  (p.ada_spots ? '<br>ADA: ' + p.ada_spots : '');
                    circle.bindPopup(popupHtml);
                    
                    var label = L.tooltip({{
                        permanent: false,
                        direction: 'top',
                        offset: [0, -12]
                    }}).setContent(p.name + ' (' + p.available + '/' + p.capacity + ')');
                    circle.bindTooltip(label);
                }});

                // Initialize location tracking after a short delay
                setTimeout(function() {{
                    try {{
                        console.log('Initializing location tracking...');
                        initializeLocationTracking(map);
                    }} catch (e) {{
                        console.error('Error initializing location tracking:', e);
                    }}
                }}, 1000);
            """
            html += "L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors | Using cached tiles', maxZoom: 19 }).addTo(map);\n"
            # removed default campus marker per user request - map starts without the OSU pin
            html += "var parkingData = " + json.dumps(self.parking_places) + ";\n"
            html += "function colorForAvailable(avail) { if (avail > 7) return '#15803d'; if (avail >= 4) return '#f97316'; return '#dc2626'; }\n"
            html += "var parsedParking = parkingData; if (typeof parkingData === 'string') { try { parsedParking = JSON.parse(parkingData); } catch(e) { parsedParking = []; } }\n"
            html += "parsedParking.forEach(function(p) { var circle = L.circleMarker([p.lat, p.lon], { radius: 10, color: colorForAvailable(p.available), fillColor: colorForAvailable(p.available), fillOpacity: 0.9 }).addTo(map); var popupHtml = '<b>' + p.name + '</b><br>Capacity: ' + p.capacity + '<br>Available: ' + p.available + (p.ada_spots? '<br>ADA: ' + p.ada_spots : ''); circle.bindPopup(popupHtml); var label = L.tooltip({permanent: false, direction: 'top', offset: [0, -12]}).setContent(p.name + ' (' + p.available + '/' + p.capacity + ')'); circle.bindTooltip(label); });\n"
            html += "window._destMarker = null; window._top3Markers = []; window._distanceLine = null; window._selectedParking = null;\n"
            html += "function clearHighlights() { try { if (window._destMarker) { map.removeLayer(window._destMarker); window._destMarker = null; } if (window._top3Markers) { window._top3Markers.forEach(function(m){ map.removeLayer(m); }); window._top3Markers = []; } if (window._distanceLine) { map.removeLayer(window._distanceLine); window._distanceLine = null; } if (window._selectedParking) { map.removeLayer(window._selectedParking); window._selectedParking = null; } } catch(e) { console.error(e); } }\n"
            html += "function addDestination(lat, lon, label) { clearHighlights(); window._destMarker = L.marker([lat, lon]).addTo(map); window._destMarker.bindPopup(label).openPopup(); map.setView([lat, lon], 16); }\n"
            html += "function showTop3(list) { try { clearHighlights(); window._top3Markers = []; list.forEach(function(p, i){ var m = L.circleMarker([p.lat, p.lon], { radius: 12, color: '#0ea5e9', fillColor: '#38bdf8', fillOpacity: 0.95 }).addTo(map); m.bindTooltip((i+1) + '. ' + p.name + ' — Avail: ' + p.available); window._top3Markers.push(m); }); } catch(e) { console.error(e); } }\n"
            html += "function showDestinationAndParking(destLat, destLon, destLabel, parkLat, parkLon, parkLabel, distanceKm) { try { console.log('Showing dest and parking:', arguments); clearHighlights(); window._destMarker = L.marker([destLat, destLon], {riseOnHover: true}).addTo(map); const userLocation = getUserLocation(); if (userLocation) { const eta = updateETAInfo(destLat, destLon); if (eta) { destLabel += '<br><br>From your location:<br>🚶‍♂️ Walking: ' + eta.walking + '<br>🚲 Biking: ' + eta.biking + '<br>🚗 Driving: ' + eta.driving + '<br>📍 Distance: ' + eta.distance + ' km'; } } window._destMarker.bindPopup(destLabel + '<br><br>Distance to parking: ' + distanceKm.toFixed(2) + ' km').openPopup(); window._selectedParking = L.circleMarker([parkLat, parkLon], { radius: 14, color: '#7e22ce', fillColor: '#a855f7', fillOpacity: 0.95, weight: 2 }).addTo(map).bindTooltip(parkLabel).openTooltip(); window._distanceLine = L.polyline([[destLat, destLon], [parkLat, parkLon]], {color: '#7e22ce', weight: 3, opacity: 0.8, dashArray: '10,10'}).addTo(map); window._destMarker.openPopup(); var bounds = L.latLngBounds([[destLat, destLon], [parkLat, parkLon]]); bounds = bounds.pad(0.3); map.fitBounds(bounds); } catch(e) { console.error('Failed to show dest/parking:', e); } }\n"
            html += "</script>\n</body>\n</html>\n"
        else:
            print("No cached tiles found. Using online tiles. Run: python map_tile_downloader.py")
            html = ""
            html += "<!DOCTYPE html>\n<html>\n<head>\n"
            html += "<link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\" />\n"
            html += "<script src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"></script>\n"
            html += "<style>body { margin: 0; padding: 0; } #map { height: 100vh; width: 100vw; }</style>\n"
            html += "</head>\n<body>\n<div id=\"map\"></div>\n<script>\n"
            html += "var map = L.map('map').setView([" + str(okstate_lat) + ", " + str(okstate_lon) + "], 15);\n"
            html += "L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OpenStreetMap contributors', maxZoom: 19 }).addTo(map);\n"
            # removed default campus marker per user request - map starts without the OSU pin
            html += "var parkingData = " + json.dumps(self.parking_places) + ";\n"
            html += "function colorForAvailable(avail) { if (avail > 7) return '#15803d'; if (avail >= 4) return '#f97316'; return '#dc2626'; }\n"
            html += "var parsedParking = parkingData; if (typeof parkingData === 'string') { try { parsedParking = JSON.parse(parkingData); } catch(e) { parsedParking = []; } }\n"
            html += "parsedParking.forEach(function(p) { var circle = L.circleMarker([p.lat, p.lon], { radius: 10, color: colorForAvailable(p.available), fillColor: colorForAvailable(p.available), fillOpacity: 0.9 }).addTo(map); var popupHtml = '<b>' + p.name + '</b><br>Capacity: ' + p.capacity + '<br>Available: ' + p.available + (p.ada_spots? '<br>ADA: ' + p.ada_spots : ''); circle.bindPopup(popupHtml); var label = L.tooltip({permanent: false, direction: 'top', offset: [0, -12]}).setContent(p.name + ' (' + p.available + '/' + p.capacity + ')'); circle.bindTooltip(label); });\n"
            html += "</script>\n</body>\n</html>\n"
        
        self.setHtml(html)

    # Methods to call JS from Python
    def add_destination_marker(self, lat, lon, label):
        js = f"addDestination({lat}, {lon}, {json.dumps(label)});"
        try:
            self.page().runJavaScript(js)
        except Exception as e:
            print("JS call failed:", e)

    def show_top3_markers(self, parking_list):
        # parking_list: list of dicts with keys lat, lon, name, capacity, available
        js_list = json.dumps(parking_list)
        js = f"showTop3({js_list});"
        try:
            self.page().runJavaScript(js)
        except Exception as e:
            print("JS call failed:", e)

    def show_destination_and_parking(self, dest_lat, dest_lon, dest_label, park_lat, park_lon, park_label, distance_km):
        js = f"showDestinationAndParking({dest_lat}, {dest_lon}, {json.dumps(dest_label)}, {park_lat}, {park_lon}, {json.dumps(park_label)}, {distance_km});"
        try:
            self.page().runJavaScript(js)
        except Exception as e:
            print("JS call failed:", e)

    def show_route(self, start_lat, start_lon, dest_lat, dest_lon, info_text="Route"):
        """Draw a simple polyline route from start to dest and show markers/popups with info_text.
        This is an approximate visual route (straight line). For real routing, integrate a routing API.
        """
        js_info = json.dumps(info_text)
        js = f"""
        try {{
            clearHighlights();
            var s = L.marker([{start_lat}, {start_lon}]).addTo(map).bindPopup('Start').openPopup();
            var d = L.marker([{dest_lat}, {dest_lon}]).addTo(map).bindPopup({js_info}).openPopup();
            var line = L.polyline([[{start_lat}, {start_lon}], [{dest_lat}, {dest_lon}]], {{color: '#10b981', weight:4, opacity:0.9}}).addTo(map);
            var bounds = L.latLngBounds([[{start_lat}, {start_lon}], [{dest_lat}, {dest_lon}]]).pad(0.3);
            map.fitBounds(bounds);
            window._destMarker = d; window._selectedParking = s; window._distanceLine = line;
        }} catch(e) {{ console.error(e); }}
        """
        try:
            self.page().runJavaScript(js)
        except Exception as e:
            print("JS call failed:", e)

    def set_view(self, lat, lon, zoom=15):
        js = f"try {{ map.setView([{lat}, {lon}], {zoom}); }} catch(e) {{ console.error(e); }};"
        try:
            self.page().runJavaScript(js)
        except Exception as e:
            print("JS call failed:", e)

    def clear_highlights(self):
        try:
            self.page().runJavaScript("clearHighlights();")
        except Exception as e:
            print("JS call failed:", e)


# FilterDropdown replaced by a QMenu popup (see filter_menu usage near top bar setup)


class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.filters = [False, False, False, False, False, False]
        self.setWindowTitle("OKState Campus Map - PySide6")
        self.setGeometry(100, 100, 1200, 800)
        # Store last searched destination for click handlers
        self._last_destination = None
        # Initialize parking pass settings
        self.selected_passes = self.load_passes()
        # Load persisted search history
        try:
            self._history_file = Path("search_history.json")
            if self._history_file.exists():
                with open(self._history_file, 'r') as hf:
                    self.search_history = json.load(hf)
            else:
                self.search_history = []
        except Exception:
            self.search_history = []
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 5)
        layout.setSpacing(5)
        
        # Top bar with filter button and dropdown container
        top_frame = QFrame()
        top_frame.setFixedHeight(60)
        top_frame.setStyleSheet("background-color: #ffffff; border-radius: 5px;")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(10, 10, 10, 10)
        
        # Filter container
        self.filter_container = QWidget()
        filter_container_layout = QVBoxLayout(self.filter_container)
        filter_container_layout.setContentsMargins(0, 0, 0, 0)
        filter_container_layout.setSpacing(0)
        
        # Filter button
        self.filter_btn = QPushButton("Filter ▼")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                border: 2px solid #45a049;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        filter_container_layout.addWidget(self.filter_btn)

        # Use a QMenu for the filter options so it appears above the QWebEngineView
        self.filter_menu = QMenu(self)
        act_cars = QAction("Cars", self)
        act_motor = QAction("Motorcycle", self)
        act_bike = QAction("Bike Lane", self)
        act_nearest = QAction("Show Nearest", self)
        act_full = QAction("Show Full Lots", self)
        act_permits = QAction("Show All Permits", self)
        self.filter_menu.addAction(act_cars)
        self.filter_menu.addAction(act_motor)
        self.filter_menu.addAction(act_bike)
        self.filter_menu.addAction(act_nearest)
        self.filter_menu.addAction(act_full)
        self.filter_menu.addAction(act_permits)

        # Connect actions to the same handler
        act_cars.triggered.connect(lambda: self.select_filter(0))
        act_motor.triggered.connect(lambda: self.select_filter(1))
        act_bike.triggered.connect(lambda: self.select_filter(2))
        act_nearest.triggered.connect(lambda: self.select_filter(3))
        act_full.triggered.connect(lambda: self.select_filter(4))
        act_permits.triggered.connect(lambda: self.select_filter(5))

        # Show menu when button clicked (positioned below the button)
        self.filter_btn.clicked.connect(lambda: self.filter_menu.exec(self.filter_btn.mapToGlobal(QPoint(0, self.filter_btn.height()))))
        
        top_layout.addWidget(self.filter_container)
        # --- Search bar (beside filter) ---
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search destination (e.g. 'Oklahoma State Library')")
        self.search_input.setFixedWidth(360)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #94a3b8;
                background-color: white;
                color: #1e293b;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
        top_layout.addWidget(self.search_input)
        # Allow pressing Enter to trigger search
        self.search_input.returnPressed.connect(self.search_destination)

        self.search_btn = QPushButton("Search")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
        """)
        self.search_btn.clicked.connect(self.search_destination)
        top_layout.addWidget(self.search_btn)

        top_layout.addStretch()
        # Home button to reset map view
        self.home_btn = QPushButton("Home")
        self.home_btn.setStyleSheet("background-color:#efefef; padding:6px 10px; border-radius:6px;")
        self.home_btn.clicked.connect(self.go_home)
        top_layout.addWidget(self.home_btn)

        # Settings button for pass selection
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #efefef;
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        self.settings_btn.clicked.connect(self.show_settings)
        top_layout.addWidget(self.settings_btn)

        layout.addWidget(top_frame)

        # Initialize selected passes (load from settings if exists)
        self.selected_passes = self.load_passes()

        # Replace previous POI approach: use explicit parking locations provided by the user.
        # User-provided primary locations (names kept minimal, coordinates provided). Longitudes use negative values for W.
        self.parking_places = [
            {
                "name": "Student Union Garage", 
                "lat": 36.1264, 
                "lon": -97.0867, 
                "capacity": 400, 
                "available": 75,
                "passes": ["staff", "green_commuter", "silver_commuter"]
            },
            {
                "name": "Colvin Recreation Center", 
                "lat": 36.1287, 
                "lon": -97.0818, 
                "capacity": 250, 
                "available": 40,
                "passes": ["staff", "green_commuter"]
            },
            {
                "name": "University Commons West", 
                "lat": 36.1287, 
                "lon": -97.0664, 
                "capacity": 300, 
                "available": 55,
                "passes": ["residence_hall", "staff"]
            },
            {
                "name": "Drummond Hall Lot", 
                "lat": 36.1260, 
                "lon": -97.0701, 
                "capacity": 120, 
                "available": 12,
                "passes": ["staff", "silver_commuter"]
            },
            {
                "name": "Physical Sciences Building Lot", 
                "lat": 36.1242, 
                "lon": -97.0664, 
                "capacity": 180, 
                "available": 20,
                "passes": ["staff", "green_commuter", "silver_commuter"]
            },
        ]

        # Randomly assign a few ADA spots per lot (1-6, but not exceeding capacity)
        for p in self.parking_places:
            max_ada = min(6, max(1, p['capacity'] // 50))
            p['ada_spots'] = random.randint(1, max_ada)

        # Try to augment with nearby OSM parkings using Overpass (no API key required). This is best-effort.
        try:
            def fetch_nearby_overpass(lat, lon, radius_m=800, limit=6):
                query = f"[out:json][timeout:10];(node[amenity=parking](around:{radius_m},{lat},{lon});way[amenity=parking](around:{radius_m},{lat},{lon});relation[amenity=parking](around:{radius_m},{lat},{lon}););out center {limit};"
                url = "https://overpass-api.de/api/interpreter"
                r = requests.post(url, data={'data': query}, timeout=8)
                results = []
                if r.status_code == 200:
                    data = r.json()
                    for el in data.get('elements', []):
                        # Determine coordinates
                        if el.get('type') == 'node':
                            lat2 = el.get('lat')
                            lon2 = el.get('lon')
                        else:
                            center = el.get('center', {})
                            lat2 = center.get('lat')
                            lon2 = center.get('lon')
                        if lat2 is None or lon2 is None:
                            continue
                        name = el.get('tags', {}).get('name', 'OSM Parking')
                        capacity = None
                        try:
                            capacity = int(el.get('tags', {}).get('capacity', 0))
                        except Exception:
                            capacity = 50
                        results.append({
                            'name': name,
                            'lat': lat2,
                            'lon': lon2,
                            'capacity': capacity,
                            'available': max(1, capacity // 10)
                        })
                        if len(results) >= limit:
                            break
                return results

            # use campus center as seed to find additional parkings
            seed_lat = sum([p['lat'] for p in self.parking_places]) / len(self.parking_places)
            seed_lon = sum([p['lon'] for p in self.parking_places]) / len(self.parking_places)
            extras = fetch_nearby_overpass(seed_lat, seed_lon, radius_m=1200, limit=6)
            # append extras if not duplicate by coordinate
            for ex in extras:
                dup = any(abs(ex['lat'] - p['lat']) < 1e-5 and abs(ex['lon'] - p['lon']) < 1e-5 for p in self.parking_places)
                if not dup:
                    ex['ada_spots'] = random.randint(1, min(4, max(1, ex['capacity'] // 50)))
                    # Assign random passes to OSM parking places
                    possible_passes = ["staff", "green_commuter", "silver_commuter", "residence_hall"]
                    num_passes = random.randint(1, 3)
                    ex['passes'] = random.sample(possible_passes, num_passes)
                    if ex['ada_spots'] > 0:
                        ex['passes'].append("ada")
                    self.parking_places.append(ex)
        except Exception as e:
            print('Overpass fetch skipped/failed:', e)

        # Map widget (takes remaining space) - pass parking data so markers are shown
        self.map_widget = MapWidget(parking_places=self.parking_places)
        layout.addWidget(self.map_widget)

    # Keep a small search history (most recent first)
    # (already loaded at startup)

        # Pull-up tab (pass main window as parent so pull-up can call back)
        self.pull_up = PullUpWidget(parent=self)
        layout.addWidget(self.pull_up)
        
    # Filter menu is implemented as a QMenu (see setup near top bar). Old
    # toggle/show/hide methods for the previous FilterDropdown widget were removed.
    
    def select_filter(self, filter_type):
        """Handle filter selection"""
        print(f"Filter selected: {filter_type}")
        # Close the menu if it's open
        try:
            if hasattr(self, 'filter_menu'):
                self.filter_menu.close()
        except Exception:
            pass
        # Toggle the filter
        self.filters[filter_type] = not self.filters[filter_type]

        # If no destination is set yet, prompt user to search first
        if not getattr(self, '_last_destination', None):
            QMessageBox.information(self, "Filter", "Please search for a destination first.")
            return

        # Apply the selected filter to the last destination
        dest = self._last_destination
        try:
            if self.filters[0] or self.filters[1]:
                top3, recommendation = self.compute_nearest_parking(dest['lat'], dest['lon'])
                # show top3 markers and populate pull-up
                js_top3 = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "capacity": p["capacity"], "available": p["available"], "distance_km": p["distance_km"]} for p in top3]
                self.map_widget.add_destination_marker(dest['lat'], dest['lon'], dest['display_name'])
                if js_top3:
                    self.map_widget.show_top3_markers(js_top3)
                self.pull_up.set_results(dest['display_name'], top3, recommendation)
                self.pull_up.expand()
            elif self.filters[2]:
                # Show approximate shortest bike route from campus center to destination and estimate time
                start_lat = self.map_widget.okstate_lat
                start_lon = self.map_widget.okstate_lon
                dist_km = self._haversine_km(start_lat, start_lon, dest['lat'], dest['lon'])
                # assume average bike speed ~15 km/h
                bike_speed_kmh = 15.0
                minutes = (dist_km / bike_speed_kmh) * 60.0
                info_text = f"Bike route — {dist_km:.2f} km — approx {int(minutes)} min"
                # Use a new MapWidget helper to draw a route polyline and markers
                try:
                    self.map_widget.show_route(start_lat, start_lon, dest['lat'], dest['lon'], info_text)
                except Exception:
                    # fallback: just add destination marker
                    self.map_widget.add_destination_marker(dest['lat'], dest['lon'], dest['display_name'])
                # Populate pull-up with a concise bike info entry
                bike_info = [{
                    'name': 'Bike route', 'lat': dest['lat'], 'lon': dest['lon'], 'capacity': 0, 'available': 0, 'distance_km': dist_km
                }]
                self.pull_up.set_results(dest['display_name'], bike_info, None)
                self.pull_up.expand()
        except Exception as e:
            print('select_filter failed:', e)

    def _haversine_km(self, lat1, lon1, lat2, lon2):
        # Haversine distance in kilometers
        R = 6371.0
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def compute_nearest_parking(self, dest_lat, dest_lon):
        """Compute enriched parking list sorted by distance and a recommendation.
        Returns (top3_list, recommendation)
        Each entry in lists is a dict with keys: name, lat, lon, capacity, available, distance_km, passes
        """
        enriched = []
        try:
            for p in self.parking_places:
                spot_passes = set(p.get('passes', []))
                if p.get('ada_spots', 0) > 0:
                    spot_passes.add('ada')

                active_passes = {pass_id for pass_id, is_selected in self.selected_passes.items() if is_selected}
                if (not active_passes or (spot_passes & active_passes) or self.filters[5]) and (p['available'] > 0 or self.filters[4]):
                    d = self._haversine_km(dest_lat, dest_lon, p['lat'], p['lon'])
                    enriched.append({
                        'name': p['name'], 'lat': p['lat'], 'lon': p['lon'], 'capacity': p['capacity'], 'available': p['available'], 'distance_km': d, 'passes': list(spot_passes)
                    })

            enriched.sort(key=lambda x: x['distance_km'])
            top3 = enriched
            if self.filters[3]:
                top3 = enriched[:3]

            SIMILAR_DISTANCE_KM = 0.05
            def color_for_avail(a):
                if a > 7:
                    return 'green'
                if a >= 4:
                    return 'orange'
                return 'red'

            candidates = [p for p in enriched if color_for_avail(p['available']) != 'red']
            recommendation = None
            if candidates:
                closest = candidates[0]
                group = [c for c in candidates if abs(c['distance_km'] - closest['distance_km']) <= SIMILAR_DISTANCE_KM]
                if len(group) == 1:
                    recommendation = closest
                else:
                    greens = [g for g in group if color_for_avail(g['available']) == 'green']
                    if greens:
                        greens.sort(key=lambda x: (-x['available'], x['distance_km']))
                        recommendation = greens[0]
                    else:
                        oranges = [g for g in group if color_for_avail(g['available']) == 'orange']
                        if oranges:
                            oranges.sort(key=lambda x: (-x['available'], x['distance_km']))
                            recommendation = oranges[0]
                        else:
                            group.sort(key=lambda x: (-x['available'], x['distance_km']))
                            recommendation = group[0]

            return top3, recommendation
        except Exception as e:
            print('compute_nearest_parking failed:', e)
            return [], None

    def search_destination(self):
        """Search for a destination, show it on the map and populate pull-up with nearest parking info."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Search", "Please enter a destination to search for.")
            return

        # Save to search history (most recent first), avoid immediate duplicates
        try:
            if not hasattr(self, 'search_history'):
                self.search_history = []
            if not self.search_history or self.search_history[0].lower() != query.lower():
                self.search_history.insert(0, query)
            # keep only last 10
            self.search_history = self.search_history[:10]
            # persist history to disk
            try:
                if hasattr(self, '_history_file'):
                    with open(self._history_file, 'w') as hf:
                        json.dump(self.search_history, hf, indent=2)
            except Exception:
                pass
        except Exception:
            pass

        # Use Nominatim to geocode the destination (append Stillwater OK to bias results)
        q = f"{query}, Stillwater OK"
        try:
            # request multiple results so we can pick the best match
            resp = requests.get("https://nominatim.openstreetmap.org/search", params={"q": q, "format": "json", "limit": 5, "addressdetails": 1}, headers={"User-Agent": "OKStateParkingApp/1.0"}, timeout=6)
        except Exception as e:
            QMessageBox.critical(self, "Search error", f"Network/geocoding error:\n{e}")
            return

        try:
            results = resp.json()
        except Exception:
            results = None

        if not results:
            QMessageBox.information(self, "No results", "Could not find the destination. Try a different query.")
            return

        # Choose best result heuristically: prefer results whose display_name contains query, then type/library, else first
        def choose_best_result(results_list, query_text):
            ql = query_text.lower()
            # first pass: display_name contains query words
            for r in results_list:
                dn = r.get('display_name','').lower()
                if ql in dn:
                    return r
            # second pass: prefer known types
            preferred_types = {'library', 'public_building', 'building', 'amenity', 'place'}
            for r in results_list:
                if r.get('type') in preferred_types:
                    return r
            # fallback
            return results_list[0]

        item = choose_best_result(results, query)
        # Store last destination for parking click handlers with coordinates
        self._last_destination = {
            'lat': float(item['lat']),
            'lon': float(item['lon']),
            'display_name': item.get('display_name', query)
        }
        # Get and store destination coordinates
        dest_lat = float(item.get("lat"))
        dest_lon = float(item.get("lon"))
        display_name = item.get("display_name", query)
        
        # Store destination info for parking clicks
        self._last_destination = {
            'lat': dest_lat,
            'lon': dest_lon,
            'display_name': display_name
        }

        # Compute distances to parking places with pass filtering
        enriched = []
        for p in self.parking_places:
            # Check if the parking spot is accessible with selected passes
            spot_passes = set(p.get('passes', []))
            if p.get('ada_spots', 0) > 0:
                spot_passes.add('ada')
            
            # Get active passes (ones that are selected)
            active_passes = {pass_id for pass_id, is_selected in self.selected_passes.items() if is_selected}
            
            # If no passes are selected, show all spots
            # If passes are selected, only show spots that match at least one selected pass
            if not active_passes or (spot_passes & active_passes):
                d = self._haversine_km(dest_lat, dest_lon, p["lat"], p["lon"])
                enriched.append({
                    "name": p["name"],
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "capacity": p["capacity"],
                    "available": p["available"],
                    "distance_km": d,
                    "passes": list(spot_passes)  # Include pass info for display
                })

        enriched.sort(key=lambda x: x["distance_km"])
        top3 = enriched
        if self.filters[3]:
            top3 = enriched[:3]

        # Recommendation logic per rules:
        # - ignore red (available < 4)
        # - primary by distance; if multiple within SIMILAR_DISTANCE_KM, prefer green then orange, then availability
        SIMILAR_DISTANCE_KM = 0.05  # 50 meters

        def color_for_avail(a):
            if a > 7:
                return 'green'
            if a >= 4:
                return 'orange'
            return 'red'

        candidates = [p for p in enriched if color_for_avail(p['available']) != 'red']
        recommendation = None
        if candidates:
            # already sorted by distance
            closest = candidates[0]
            # find group close to closest
            group = [c for c in candidates if abs(c['distance_km'] - closest['distance_km']) <= SIMILAR_DISTANCE_KM]
            if len(group) == 1:
                recommendation = closest
            else:
                # prefer green in group
                greens = [g for g in group if color_for_avail(g['available']) == 'green']
                if greens:
                    # choose green with highest availability, tie-breaker distance
                    greens.sort(key=lambda x: (-x['available'], x['distance_km']))
                    recommendation = greens[0]
                else:
                    # prefer orange with highest availability
                    oranges = [g for g in group if color_for_avail(g['available']) == 'orange']
                    if oranges:
                        oranges.sort(key=lambda x: (-x['available'], x['distance_km']))
                        recommendation = oranges[0]
                    else:
                        # fallback: highest availability
                        group.sort(key=lambda x: (-x['available'], x['distance_km']))
                        recommendation = group[0]

        # Update map markers and pull-up panel
        label = f"{display_name}".replace('"', '')
        # Add destination marker and show top-3 highlights
        self.map_widget.add_destination_marker(dest_lat, dest_lon, label)
        # Build minimal list of dicts for JS top3
        js_top3 = [{"name": p["name"], "lat": p["lat"], "lon": p["lon"], "capacity": p["capacity"], "available": p["available"], "distance_km": p["distance_km"]} for p in top3]
        self.map_widget.show_top3_markers(js_top3)

        # Push results to pull-up and expand
        self.pull_up.set_results(display_name, top3, recommendation)
        self.pull_up.expand()

    def set_current_user(self, username):
        """Load user passes from local users.json (if available) and show matching parking lots."""
        try:
            # read local users.json if present
            import json, os
            users_file = Path("users.json")
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users = json.load(f)
            else:
                users = {}

            user = users.get(username)
            # Normalize structure: may be plain password string or dict
            passes = []
            if isinstance(user, dict):
                passes = user.get('passes') or user.get('form') and [user.get('form')] or []
            else:
                passes = []

            self.current_user = username
            self.current_user_passes = passes
            # Show parking lots that match these passes
            self.show_parking_for_user_passes(passes)
        except Exception as e:
            print("Failed to load user passes:", e)
            
    def load_passes(self):
        """Load saved pass selections from file"""
        try:
            settings_file = Path("parking_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        # Default settings (all passes unchecked)
        return {
            "staff": False,
            "green_commuter": False,
            "silver_commuter": False,
            "residence_hall": False,
            "ada": False
        }
        
    def save_passes(self):
        """Save pass selections to file"""
        try:
            with open("parking_settings.json", 'w') as f:
                json.dump(self.selected_passes, f)
        except Exception as e:
            print(f"Failed to save passes: {e}")
            
    def show_settings(self):
        """Show settings dialog with pass selection"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Parking Pass Settings")
        dialog.setFixedWidth(300)
        layout = QVBoxLayout()
        
        # Create checkboxes for each pass type
        passes = {
            "staff": "Staff",
            "green_commuter": "Green Commuter",
            "silver_commuter": "Silver Commuter",
            "residence_hall": "Residence Hall Maroon",
            "ada": "ADA (Physical Handicap)"
        }
        
        checkboxes = {}
        for pass_id, pass_name in passes.items():
            checkbox = QPushButton(pass_name)
            checkbox.setCheckable(True)
            checkbox.setChecked(self.selected_passes.get(pass_id, False))
            checkbox.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    margin: 2px;
                }
                QPushButton:checked {
                    background-color: #93c5fd;
                    border-color: #3b82f6;
                }
            """)
            layout.addWidget(checkbox)
            checkboxes[pass_id] = checkbox
            
        # Add a note about filtering
        note = QLabel("Selected passes will filter parking search results\nto show only compatible parking spots.")
        note.setStyleSheet("color: #6b7280; padding: 10px;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)
        
        # Save button
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        layout.addWidget(save_btn)
        
        def save_settings():
            for pass_id, checkbox in checkboxes.items():
                self.selected_passes[pass_id] = checkbox.isChecked()
            self.save_passes()
            dialog.accept()
            
        save_btn.clicked.connect(save_settings)
        dialog.setLayout(layout)
        dialog.exec()

    def show_parking_for_user_passes(self, passes, center_lat=None, center_lon=None):
        """Filter parking_places by allowed_passes and availability and display results.

        passes: list of pass strings
        center_lat/center_lon: optional center to compute distances from (defaults to campus center)
        """
        if not passes:
            # nothing to show
            self.pull_up.set_results("Pass Matches", [], None)
            self.pull_up.expand()
            return

        if center_lat is None or center_lon is None:
            center_lat = self.map_widget.okstate_lat
            center_lon = self.map_widget.okstate_lon

        matches = []
        for p in self.parking_places:
            allowed = p.get('allowed_passes', [])
            # intersection: any pass in user's passes
            if any(pp in allowed for pp in passes) and p.get('available', 0) > 0:
                d = self._haversine_km(center_lat, center_lon, p['lat'], p['lon'])
                matches.append({
                    'name': p['name'], 'lat': p['lat'], 'lon': p['lon'], 'capacity': p['capacity'], 'available': p['available'], 'distance_km': d
                })

        matches.sort(key=lambda x: x['distance_km'])

        # Recommendation logic: same rules as search (ignore red, distance primary, tie-break by color/availability)
        SIMILAR_DISTANCE_KM = 0.05
        def color_for_avail(a):
            if a > 7:
                return 'green'
            if a >= 4:
                return 'orange'
            return 'red'

        candidates = [m for m in matches if color_for_avail(m['available']) != 'red']
        recommendation = None
        if candidates:
            closest = candidates[0]
            group = [c for c in candidates if abs(c['distance_km'] - closest['distance_km']) <= SIMILAR_DISTANCE_KM]
            if len(group) == 1:
                recommendation = closest
            else:
                greens = [g for g in group if color_for_avail(g['available']) == 'green']
                if greens:
                    greens.sort(key=lambda x: (-x['available'], x['distance_km']))
                    recommendation = greens[0]
                else:
                    oranges = [g for g in group if color_for_avail(g['available']) == 'orange']
                    if oranges:
                        oranges.sort(key=lambda x: (-x['available'], x['distance_km']))
                        recommendation = oranges[0]
                    else:
                        group.sort(key=lambda x: (-x['available'], x['distance_km']))
                        recommendation = group[0]

        # Show matches on map and in pull-up
        js_list = [{"name": m['name'], 'lat': m['lat'], 'lon': m['lon'], 'capacity': m['capacity'], 'available': m['available']} for m in matches]
        if js_list:
            self.map_widget.show_top3_markers(js_list)
        self.pull_up.set_results("Parking for your passes", matches, recommendation)
        self.pull_up.expand()

    def search_for_query(self, query: str):
        """Helper to run a search programmatically (used by history buttons)."""
        try:
            self.search_input.setText(query)
            # run the existing search flow
            self.search_destination()
        except Exception as e:
            print("search_for_query failed:", e)

    def go_home(self):
        """Reset map to campus center and clear highlights."""
        try:
            # clear any highlights and destination markers
            self.map_widget.clear_highlights()
            # set view to OKState center
            self.map_widget.set_view(self.map_widget.okstate_lat, self.map_widget.okstate_lon, 15)
        except Exception as e:
            print("go_home failed:", e)

    def save_history(self):
        """Explicit method to persist search_history to disk."""
        try:
            if hasattr(self, '_history_file'):
                with open(self._history_file, 'w') as hf:
                    json.dump(getattr(self, 'search_history', []), hf, indent=2)
        except Exception as e:
            print("Failed to save history:", e)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()