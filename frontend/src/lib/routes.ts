import { selectedTheme } from "$lib/store/theme.store";
import { get } from "svelte/store";
import { base } from "$app/paths";

export type RouteItem = {
  name: string;
  key: string;
  path: string;
};

export type Route = {
  [key: string]: RouteItem;
};

export const routes: Route = {
  themis: {
    key: "themis",
    name: "Themis",
    path: `${base}/main/themis`,
  },
  schemaEditor: {
    key: "schemaEditor",
    name: "Schema Editor",
    path: `${base}/main/themis`,
  },
  viewSchemaInstance: {
    key: "viewSchemaInstance",
    name: "View Schema Instance",
    path: `${base}/main/themis/view/:document_id`,
  },
  home: {
    key: "home",
    name: "Home",
    path: `${base}/`,
  },
  missions: {
    key: "missions",
    name: "Missions",
    path: `${base}/missions`,
  },
  login: {
    key: "login",
    name: "Login",
    path: `${base}/login`, // Updated path
  },
  register: {
    key: "register",
    name: "Register",
    path: `${base}/register`, // Updated path
  },
  terms: {
    key: "terms",
    name: "Terms and Conditions",
    path: `${base}/terms`,
  },
  privacy: {
    key: "privacy",
    name: "Privacy Policy",
    path: `${base}/privacy`,
  },
  verifyEmail: {
    key: "verifyEmail",
    name: "Verify Email",
    path: `${base}/verify-email`, // Updated path
  },
  contact: {
    key: "contact",
    name: "Contact",
    path: `${base}/contact`, // Assuming this is not under /auth
  },
  forgotPassword: {
    key: "forgotPassword",
    name: "Forgot Password",
    path: `${base}/forgot-password`, // Updated path
  },
  resetPassword: {
    key: "resetPassword",
    name: "Reset Password",
    path: `${base}/reset-password`, // Updated path
  },
  resetPasswordConfirm: {
    key: "resetPasswordConfirm",
    name: "Reset Password Confirm",
    path: `${base}/reset-password-confirm`, // New path for confirmation
  },
  logout: {
    key: "logout",
    name: "Logout",
    path: `${base}/logout`, // Updated path
  },
  settings: {
    key: "settings",
    name: "Settings",
    path: `${base}/settings`,
  },
  main: {
    key: "main",
    name: "Main",
    path: get(selectedTheme).mainRoute
      ? get(selectedTheme).mainRoute
      : `${base}/`,
  },
  invoice: {
    key: "invoice",
    name: "invoice",
    path: `${base}/main/contracts/:contract_id/shipments/:shipment_id/invoice/:invoice_id`, // TODO: test
  },
  provisional: {
    key: "provisional",
    name: "provisional",
    path: `${base}/main/contracts/contract/:contract_id/shipments/:shipment_id/provisional/:provisional_id`, // TODO: test
  },
  final: {
    key: "final",
    name: "final",
    path: `${base}/main/contracts/contract/:contract_id/shipments/:shipment_id/final/:provisional_id`, // TODO: test
  },
  hedge: {
    key: "hedge",
    name: "hedge",
    path: `${base}/main/contracts/contract/:contract_id/shipments/:shipment_id/hedge`, // TODO: test
  },
  assay: {
    key: "assay",
    name: "assay",
    path: `${base}/main/contracts/contract/:contract_id/shipments/:shipment_id/assay/:assay_id`, // TODO: test
  },
  assayVerify: {
    key: "assayVerify",
    name: "assayVerify",
    path: `${base}/main/contracts/contract/:contract_id/shipments/:shipment_id/assay/:assay_id/verify`, // TODO: test
  },
  parcel: {
    key: "parcel",
    name: "Parcel",
    path: `${base}/main/parcel`,
  },
  parcelDetail: {
    key: "parcelDetail",
    name: "ParcelDetail",
    path: `${base}/main/parcel/:parcel_id`,
  },
  parcelShipments: {
    key: "parcelShipments",
    name: "ParcelShipments",
    path: `${base}/main/parcel/:parcel_id/shipments`,
  },
} as const;

// use this to check if we have disabled a particular feature
export function routeAllowed(key: string) {
  // all the routes that can be disabled should be in the "main" folder
  return !get(selectedTheme).disabledRoutes.includes(key);
}

export type RouteKey = keyof typeof routes;
