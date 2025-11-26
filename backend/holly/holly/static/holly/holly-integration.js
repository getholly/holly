/**
 * Holly App Integration Script
 *
 * This script initializes and loads the Holly Svelte app into the Django template.
 */
console.log('calling holly-integration.js')
// document.addEventListener('DOMContentLoaded', function() {
//   // Target div for mounting the Svelte app
//   const hollyAppContainer = document.getElementById('holly-app')
//
//   if (!hollyAppContainer) {
//     console.error('Holly app container not found')
//     return
//   }
//
//   // Extract user data from data attributes
//   const userData = {
//     username: hollyAppContainer.getAttribute('data-username'),
//     email: hollyAppContainer.getAttribute('data-email'),
//     csrfToken: hollyAppContainer.getAttribute('data-csrftoken'),
//     availableLlms: JSON.parse(hollyAppContainer.getAttribute('data-available-llms') || '[]')
//   }
//
//   // Fetch additional configuration from the server
//   fetch('/_holly/credentials/')
//     .then(response => response.json())
//     .then(data => {
//       // Merge server data with userData
//       const appConfig = { ...userData, ...data }
//
//       // Initialize the Holly Svelte app
//       console.log('Initializing Holly app with configuration:', appConfig)
//
//       // Remove loading placeholder
//       while (hollyAppContainer.firstChild) {
//         hollyAppContainer.removeChild(hollyAppContainer.firstChild)
//       }
//
//       // Mount the Svelte app
//       // This assumes your Svelte app is built and available at the specified path
//       import('/static/js/holly-app/main.js')
//         .then(module => {
//           const HollyApp = module.default
//
//           new HollyApp({
//             target: hollyAppContainer,
//             props: appConfig
//           })
//         })
//         .catch(error => {
//           console.error('Failed to load Holly Svelte app:', error)
//
//           // Show error message in the container
//           hollyAppContainer.innerHTML = `
//             <div class="flex items-center justify-center h-full">
//               <div class="text-center p-6 max-w-md bg-white rounded-lg border border-red-200 shadow-md">
//                 <svg class="mx-auto mb-4 w-14 h-14 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
//                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
//                 </svg>
//                 <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900">Failed to load Holly app</h5>
//                 <p class="mb-3 font-normal text-gray-700">
//                   There was an error loading the Holly application. Please check the console for more details.
//                 </p>
//                 <a href="javascript:location.reload()" class="inline-flex items-center py-2 px-3 text-sm font-medium text-center text-white bg-blue-700 rounded-lg hover:bg-blue-800 focus:ring-4 focus:ring-blue-300">
//                   Retry
//                   <svg class="ml-2 -mr-1 w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
//                     <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path>
//                   </svg>
//                 </a>
//               </div>
//             </div>
//           `
//         })
//     })
//     .catch(error => {
//       console.error('Failed to fetch credentials:', error)
//       hollyAppContainer.innerHTML = `
//         <div class="flex items-center justify-center h-full">
//           <div class="text-center p-6 max-w-md bg-white rounded-lg border border-red-200 shadow-md">
//             <svg class="mx-auto mb-4 w-14 h-14 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
//               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
//             </svg>
//             <h5 class="mb-2 text-2xl font-bold tracking-tight text-gray-900">Authentication Error</h5>
//             <p class="mb-3 font-normal text-gray-700">
//               Unable to fetch credentials. Please make sure you are logged in and try again.
//             </p>
//             <a href="/_accounts/login/" class="inline-flex items-center py-2 px-3 text-sm font-medium text-center text-white bg-blue-700 rounded-lg hover:bg-blue-800 focus:ring-4 focus:ring-blue-300">
//               Login
//               <svg class="ml-2 -mr-1 w-4 h-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
//                 <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"></path>
//               </svg>
//             </a>
//           </div>
//         </div>
//       `
//     })
// })
