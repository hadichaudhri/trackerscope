import { useEffect } from "react";

export default function LocalStorage() {
    useEffect(() => {
        localStorage.setItem("userID", "1234");
    });

    return (
        <>
            <h1 on>Local Storage</h1>
            <p>
                Local storage is a web storage object that allows data to be
                stored in the user&apos;s browser. Data stored in local storage
                has no expiration time and will persist after the browser window
                is closed.
            </p>
        </>
    );
}
