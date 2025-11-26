import { goto } from "$app/navigation";
import { routes } from "$lib/routes";
import {
  displayErrorMessage,
  modalErrorMessage,
} from "$lib/store/error/errorMessage.store";

export async function checkError(error: Error, messagePrefix: string = "") {
  /*
	Agreed Code Meaning:
	401 -> login incorrect, access token expired, password incorrect, etc
	422 -> backend out of sync, LLM re-extract, or verify_mapping new field, etc
	 */
  console.error(`Error: ${error}`);
  if (error.response) {
    const body = await error.response.json();
    const detail = Object.prototype.hasOwnProperty.call(body, "detail")
      ? body.detail
      : "";

    console.error(`${messagePrefix} failed with error:${detail}`);
    if (error.response.status === 401) {
      await goto(routes.logout.path);
    } else if (error.response.status === 422) {
      // TODO: display toast/popup to say we got invalid error:
      const errorMsg = `Invalid Response Received. Error: ${JSON.stringify(error.response.status)}`;
      console.error(errorMsg);
      modalErrorMessage.set(errorMsg);
      displayErrorMessage.set(true);
    } else if (error.response.status === 415) {
      const errorMsg = `Problem with uploading file - is it of correct format or is it corrupted? Error:${JSON.stringify(error.response.status)}`;
      console.error(errorMsg);
      modalErrorMessage.set(errorMsg);
      displayErrorMessage.set(true);
    } else if (error.response.status === 400) {
      const errorMsg = `Server returned 400: ${detail}`;
      modalErrorMessage.set(errorMsg);
      displayErrorMessage.set(true);
    } else {
      throw error;
    }
  } else {
    throw error;
  }
}
