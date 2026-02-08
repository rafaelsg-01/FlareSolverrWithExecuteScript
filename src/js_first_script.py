Js_firstScriptImport = """
if (!location.href.includes("#_disableFirstScript")) {
    console.log('Exec -> _enableFirstScript')
    const limite = 1763962190000 + (2 * 60 * 1000); // timestamp + 2 minutos

    // Bypass DisableDevtool
    if (location.href.includes("#_execScript_bypassDisableDevtool")) {
        console.log('Exec -> _execScript_bypassDisableDevtool')

        let _documentWrite = document.write.bind(document)
        document.write = function (html) {
            html = html.replace('already running");', 'already running");return;')
            _documentWrite(html)
        }
    }

    // Set Headers Rede Canais (Cookie and Service Worker)
    if (location.href.includes("#_execScript_setHeadersRedeCanais") && Date.now() > limite) {
        console.log('Exec -> _execScript_setHeadersRedeCanais')

        window._waitNewPromise = new Promise((resolve) => {
            const pFetch = fetch("/che")
                .then(() => console.log("Fetch /che completed"))
                .catch((e) => console.error("Fetch error: " + e))

            const pRegister = navigator.serviceWorker.register("/sw.js")
                .then((reg) => {
                    console.log("Service Worker registered")
                    return navigator.serviceWorker.ready
                })
                .then(() => console.log("Service Worker activated"))
                .catch((e) => console.error("Service Worker error: " + e))

            Promise.allSettled([pFetch, pRegister]).then(() => {
                console.log("All processes completed.")
                resolve(true)
            })
        })
    }

    // Set Headers Novibet (Cookie and Service Worker)
    if (location.href.includes("#_execScript_setHeadersNovibet")) {
        console.log('Exec -> _execScript_setHeadersNovibet')

        window._waitNewPromise = new Promise((resolve) => {
            const pFetch = fetch("https://www.novibet.bet.br/ngapi/desktop/pt/userAccount/registration-get-model", {
                    "headers": {
                        "content-type": "application/json"
                    },
                    "body": JSON.stringify({
                        "bannerModel": {
                            "affiliateId": null,
                            "channel": "desktop",
                            "folderPath": "site-banners/registration-banners",
                            "path": "default",
                            "landingId": null,
                            "pageType": "sports"
                        },
                        "affiliationModel": {
                            "affC": null,
                            "btagC": null,
                            "campC": null,
                            "promoCode": null
                        }
                    }),
                    "method": "POST"
                })
                .then(() => console.log("Fetch /novibet completed"))
                .catch((e) => console.error("Fetch error: " + e))

            Promise.allSettled([pFetch]).then(() => {
                console.log("All processes completed.")
                resolve(true)
            })
        })
    }
}
"""