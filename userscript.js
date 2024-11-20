// ==UserScript==
// @name         Cookie and LocalStorage Detector
// @namespace    http://tampermonkey.net/
// @version      1.1
// @description  Detect if a website has attached cookies or uses localStorage
// @author       Hadi Chaudhri, Holly Zhuang, Yihong Song
// @match        *://*/*
// @grant        GM_registerMenuCommand
// @grant        GM_cookie
// ==/UserScript==

// would normally have this, but uses ES6 modules :(
// @require      https://openfpcdn.io/fingerprintjs/v4

(function () {
    "use strict";

    //     const fp = await FingerprintJS.load();
    //     return await fp.get();
    // }

    async function getCookies() {
        return new Promise((resolve) => {
            GM_cookie.list({}, (cookies) => {
                if (cookies && cookies.length > 0) {
                    const cookieList = cookies.map(
                        (cookie) => `<li>${cookie.name}: ${cookie.value}</li>`
                    );
                    resolve(cookieList);
                } else {
                    resolve(["<li>No cookies detected.</li>"]);
                }
            });
        });
    }

    function getLocalStorageData() {
        let localStorageData = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            const value = localStorage.getItem(key);
            localStorageData.push(`<li>${key}: ${value}</li>`);
        }
        return localStorageData.length > 0
            ? localStorageData
            : ["<li>No LocalStorage data detected.</li>"];
    }

    async function detectWebsiteData() {
        const cookies = await getCookies();
        const localStorageData = getLocalStorageData();
        // const fingerprint = await getFingerprint();

        const htmlContent = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Website Data</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 20px;
                        line-height: 1.6;
                    }
                    h1 {
                        color: #333;
                    }
                    ul {
                        list-style: none;
                        padding: 0;
                    }
                    li {
                        margin: 5px 0;
                        background: #f4f4f4;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }
                </style>
            </head>
            <body>
                <h1>Website Data</h1>
                <h2>Cookies</h2>
                <ul>${cookies.join("")}</ul>
                <h2>LocalStorage</h2>
                <ul>${localStorageData.join("")}</ul>
            </body>
            </html>
        `;

        const newWindow = window.open();
        newWindow.document.open();
        newWindow.document.write(htmlContent);
        newWindow.document.close();
    }

    GM_registerMenuCommand("Detect Website Data", detectWebsiteData);
})();
