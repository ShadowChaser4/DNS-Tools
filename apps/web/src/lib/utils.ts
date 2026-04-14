import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface DeviceInfo {
  deviceType: "Mobile" | "Desktop" | "Tablet" | "Unknown";
  browser: string;
  os: string;
}

const getDeviceType = (userAgent: string): DeviceInfo["deviceType"] => {
  const ua = userAgent.toLowerCase();
  if (
    /mobile|android|iphone|ipad|ipod|blackberry|iemobile|opera mini/.test(ua)
  ) {
    return "Mobile";
  } else if (/tablet|ipad/.test(ua)) {
    return "Tablet";
  } else if (/windows|macintosh|linux/.test(ua)) {
    return "Desktop";
  } else {
    return "Unknown";
  }
};

const getOsType = (userAgent: string): DeviceInfo["os"] => {
  const ua = userAgent.toLowerCase();
  if (/windows nt/.test(ua)) {
    return "Windows";
  } else if (/mac os x/.test(ua)) {
    return "macOS";
  } else if (/android/.test(ua)) {
    return "Android";
  } else if (/linux/.test(ua)) {
    return "Linux";
  } else {
    return "Unknown";
  }
};

const getBrowserType = (userAgent: string): DeviceInfo["browser"] => {
  const ua = userAgent.toLowerCase();
  if (/chrome|crios/.test(ua) && !/edge|edg|opr|opera/.test(ua)) {
    return "Chrome";
  } else if (/safari/.test(ua) && !/chrome|crios/.test(ua)) {
    return "Safari";
  } else if (/firefox|fxios/.test(ua)) {
    return "Firefox";
  } else if (/edge|edg/.test(ua)) {
    return "Edge";
  } else if (/opr|opera/.test(ua)) {
    return "Opera";
  } else {
    return "Unknown";
  }
};

export const identifyDeviceFromUserAgent = (userAgent: string): DeviceInfo => {
  const ua = userAgent.toLowerCase();
  const deviceInfo: DeviceInfo = {} as DeviceInfo;

  deviceInfo.deviceType = getDeviceType(ua);
  deviceInfo.os = getOsType(ua);
  deviceInfo.browser = getBrowserType(ua);

  return deviceInfo;
};
