import whois from "whois-ux";

export default async (req, res) => {
    // Get the ip from the query string
    const ip = req.query.ip;
    console.log("IP Address:", ip);

    // Get the WHOIS data for the IP address
    whois.whois(ip, function (err, data) {
        if (err) {
            console.error(err);
            res.status(500).json({
                error: "Internal Server Error",
                details: err.message,
            });
            return;
        }
        console.log(JSON.stringify(data));
        res.status(200).json(data);
    });
};
