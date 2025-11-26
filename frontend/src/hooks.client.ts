// code that will be run on startup

import {
  baseURL,
  cfPagesBranch,
  cfPagesCommitSha,
  serverName,
} from "$lib/apis/api.config";
// import { H } from "highlight.run"
console.log("[HOOKS-CLIENT] Starting hooks.client.ts");

if (import.meta.env.MODE === "production") {
  // H.init("odzxn0le", {
  // 	environment: baseURL,
  // 	version: `${cfPagesBranch}/${cfPagesCommitSha}`,
  // 	//tracingOrigins: true,
  // 	tracingOrigins: [
  // 		"localhost",
  // 		"githubme-app.com/api/",
  // 		`${serverName}/api`,
  // 	],
  // 	networkRecording: {
  // 		enabled: true,
  // 		recordHeadersAndBody: true,
  // 		urlBlocklist: [
  // 			// insert full or partial urls that you don't want to record here
  // 			// Out of the box, Highlight will not record these URLs (they can be safely removed):
  // 			"https://www.googleapis.com/identitytoolkit",
  // 			"https://securetoken.googleapis.com",
  // 		],
  // 	},
  // })
} else {
  // H.init("odzxn0le", {
  // 	environment: "development",
  // 	version: `${cfPagesBranch}/${cfPagesCommitSha}`,
  // 	//tracingOrigins: true,
  // 	tracingOrigins: [
  // 		"localhost",
  // 		"dev.githubme-app.com/api/",
  // 		`${serverName}/api`,
  // 	],
  // 	networkRecording: {
  // 		enabled: true,
  // 		recordHeadersAndBody: true,
  // 		urlBlocklist: [
  // 			// insert full or partial urls that you don't want to record here
  // 			// Out of the box, Highlight will not record these URLs (they can be safely removed):
  // 			"https://www.googleapis.com/identitytoolkit",
  // 			"https://securetoken.googleapis.com",
  // 		],
  // 	},
  // })
}
