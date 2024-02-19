export async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ####################
// ### EASY ROUTING ###
// ####################

let port = ':10000';
const localhost = ['0.0.0.0', 'localhost', '127.0.0.1'];

const currApiHost = window.location.hostname;

const errorUrlLocal = window.location.protocol + `//${currApiHost}${port}/404`;
const appApiUrlLocal = window.location.protocol + `//${currApiHost}${port}/api`;

const errorUrlHosted = window.location.protocol + `//${currApiHost}/404`;
const appApiUrlHosted = window.location.protocol + `//${currApiHost}/api`;

export function route(r) {
  let appApiUrl = appApiUrlHosted;
  let errorUrl= errorUrlHosted;

  for (let host of localhost) {
    if (currApiHost.indexOf(host) == 0) {
      appApiUrl = appApiUrlLocal;
      errorUrl= errorUrlLocal;
      break;
    }
  }

  if (r.indexOf('app/') == 0) {
    return `${appApiUrl}/${r}/`;
  }
  else {
    return `${errorUrl}/${r}/`;
  }
}

// ####################
// ## INTERCEPTOR DP ##
// ####################

export async function attempt(apiRoute, data={}, CRUD='GET') {
  try {
    let resp = null;

    if (CRUD == 'GET') {
      resp = await fetch(route(apiRoute)).then(r => r.json());
    }

    else if (CRUD == 'POST') {
      resp = await fetch(route(apiRoute), {
        method: CRUD,
        body: JSON.stringify(data)
      }).then(r => r.json());
    }

    else {
      console.log(`Unkown ${CRUD} request`);
      return { status: false, content: { status: 'CRUD_ERROR', error: `CRUD ${CRUD} inconnue`} };
    }

    if (!(['SUCCESS', 'DONE', 'ONGOING'].includes(resp.status))) {
      console.log(`Request to ${apiRoute} failed with parameters ${JSON.stringify(data)}: ${resp.error}`);
      return { status: false, content: resp };
    }

    return { status: true, content: resp };

  } catch (error) {
    console.log(`Error ${apiRoute} : ${error}`);
    return { status: false, content: { status: 'SERVER_ERROR', error: `API ${apiRoute} unreachable: ${error}`} };
  }
}

// ####################
// # CONFIG  FETCHING #
// ####################

// https://stackoverflow.com/questions/66190949/how-can-a-buefy-toast-be-made-available-to-all-components-in-a-vue-app
export async function initConfig() {
  try {
    const res_config = await fetch(route('app/get_config')).then(r => r.json());
    const config = res_config;
    return config;
  }
  catch (error) {
    console.log(`Error initConfig : ${error}`);
    return { };
  }
}
