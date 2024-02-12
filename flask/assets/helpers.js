export async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// ####################
// ### EASY ROUTING ###
// ####################

const currApiHost = window.location.hostname
const errorUrl = window.location.protocol + `//${currApiHost}:5000/404`
const appApiUrl = window.location.protocol + `//${currApiHost}:5000/api`

export function route(r) {
  if (r.indexOf('app/')==0) {
    return `${appApiUrl}/${r}/`
  }
  else {
    return `${errorUrl}/${r}/`
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
      return { status: false, content: { status: 'CRUD_ERROR', error: `CRUD ${CRUD} inconnue`} }
    }

    if (!(['SUCCESS', 'DONE', 'ONGOING'].includes(resp.status))) {
      console.log(`Request to ${apiRoute} failed with parameters ${JSON.stringify(data)}: ${resp.error}`);
      return { status: false, content: resp };
    }

    return { status: true, content: resp }

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
    const res_config = await fetch(route('app/get_config')).then(r => r.json())
    const config = res_config
    return config
  }
  catch (error) {
    console.log(`Error initConfig : ${error}`)
    return {}
  }
}
