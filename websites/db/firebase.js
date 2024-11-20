// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";

import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyARJiKr_iPh7hiywZCWIo86al_WPfN6oH4",
    authDomain: "musaic1.firebaseapp.com",
    databaseURL: "https://musaic1-default-rtdb.firebaseio.com",
    projectId: "musaic1",
    storageBucket: "musaic1.firebasestorage.app",
    messagingSenderId: "62100760514",
    appId: "1:62100760514:web:ca4ab577d5c8aaa55fd85b",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Get a Firestore instance
const db = getFirestore(app);

export { db };
