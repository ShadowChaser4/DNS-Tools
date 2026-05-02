"use client";

import { useDnsServers } from "@/lib/hooks/dns/useDnsServers";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
} from "react-simple-maps";
import { useEffect, useState } from "react";

const GEO_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

const WorldMap = () => {
  const { data, error, isLoading } = useDnsServers();
  if (error) {
    console.error("Error fetching DNS servers:", error);
  }

  const pointers = data?.map(({ name, location }) => {
    const coords: [number, number] = [
      // round coordinates to fixed precision to avoid tiny float differences
      Number(location.coordinates[0].toFixed(6)),
      Number(location.coordinates[1].toFixed(6)),
    ];
    return {
      name,
      coords,
      type: "loading",
    };
  });

  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="w-full h-105 md:h-150">
      {mounted ? (
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

          {!isLoading &&
            pointers?.map(({ name, coords, type }) => (
              <Marker key={name} coordinates={coords}>
                <g className="group cursor-pointer">
                  <circle
                    r={5}
                    fill={
                      type === "loading"
                        ? "#FYO"
                        : type === "error"
                          ? "#F00"
                          : "#0F0"
                    }
                    stroke="#fff"
                    strokeWidth={1.5}
                  />
                  <text
                    textAnchor="middle"
                    y={-10}
                    fontSize={10}
                    fill="currentColor"
                    className="text-xs text-gray-700 opacity-0 group-hover:opacity-100 transition-opacity duration-150"
                  >
                    {name}
                  </text>
                </g>
              </Marker>
            ))}
        </ComposableMap>
      ) : (
        // placeholder to keep layout during SSR
        <div className="w-full h-full bg-gray-50" />
      )}
    </div>
  );
};

export default WorldMap;
