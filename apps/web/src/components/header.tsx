import { headers } from "next/headers";

import { identifyDeviceFromUserAgent } from "@/lib/utils";

const Header = async () => {
  const headersList = await headers();
  const userAgent = headersList.get("user-agent") || "Unknown";
  const ip =
    headersList.get("x-forwarded-for")?.split(",")[0] ||
    headersList.get("x-real-ip");

  const { deviceType, browser, os } =
    await identifyDeviceFromUserAgent(userAgent);

  return (
    <header className="bg-primary flex w-full p-4 mb-6 flex-col">
      <h1 className="text-2xl font-bold text-primary-foreground">
        DNS Heartbeat
      </h1>
      <p className="text-sm text-primary-foreground/80 mt-1">
        Your IP: {ip || "Unknown"} | Device: {deviceType} | Browser: {browser} |
        OS: {os}
      </p>
    </header>
  );
};

export default Header;
