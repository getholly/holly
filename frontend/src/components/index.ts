import type { MissionCreate } from "holly-api";
import { createMission } from "$lib/apis/mission/api.mission";
import { currentMission } from "$lib/store/mission/mission.store";
import { goto } from "$app/navigation";
import { base } from "$app/paths";

export * from "./navbar";
export async function navigateToAdvanced() {
  try {
    const missionData: MissionCreate = {
      title: "Advanced Mission",
      description: "Mission created from advanced mode",
      branch_name: `advanced-${new Date().getTime()}`,
    };
    const createdMission = await createMission(missionData);
    currentMission.set(createdMission);
    goto(`${base}/sse-chat`);
  } catch (error) {
    console.error("Error creating mission:", error);
    goto(`${base}/sse-chat`);
  }
}
