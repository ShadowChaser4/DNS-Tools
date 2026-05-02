"use client";

import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";

const GEO_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const markers: { name: string; coords: [number, number] }[] = [
  { name: "NYC", coords: [-74.006, 40.7128] },
  { name: "London", coords: [-0.1278, 51.5074] },
  { name: "Tokyo", coords: [139.6917, 35.6895] },
  { name: "Kathmandu", coords: [85.324, 27.7172] },
];

const WorldMap = () => {
  return (
    <div className="w-full h-[420px] md:h-[600px]">
      <ComposableMap style={{ width: "100%", height: "100%" }}>
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                fill="#EAEAEC"
                stroke="#D6D6DA"
              />
            ))
          }
        </Geographies>

        {markers.map(({ name, coords }) => (
          <Marker key={name} coordinates={coords}>
            <circle r={5} fill="#F53" stroke="#fff" strokeWidth={1.5} />
            <text
              textAnchor="middle"
              y={-10}
              fontSize={10}
              fill="currentColor"
              className="text-xs text-gray-700"
            >
              {name}
            </text>
          </Marker>
        ))}
      </ComposableMap>
    </div>
  );
};

export default WorldMap;
