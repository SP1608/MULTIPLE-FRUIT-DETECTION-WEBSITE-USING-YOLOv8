var express=require("express")
var bodyParser=require("body-parser")
var mongoose=require("mongoose")

const app=express()


app.use(bodyParser.json())
app.use(express.static('public'))
app.use(express.urlencoded({extended:false}))

mongoose.connect('mongodb://localhost:27017/Database')
var db=mongoose.connection
db.on('error',()=> console.log("Error in connecting to Database"))
db.once('open',()=> console.log("Connected to Database"))

// app.post("/feedback",(req,response) =>{
//     var name= req.body.name
//     var email=req.body.email
//     var enter_your_opinions_here=req.body.enter_your_opinions_here

//     var data={
//         "name":name,
//         "email":email,
//         "enter_your_opinions_here":enter_your_opinions_here
//     }
//     db.collection('users').insertOne(data,(error,collection) =>{
//         if (error){
//             throw error;
//         }
//         console.log("Record inserted successfully")
//     })
//     return response.redirect('feedback_success.html')
// })
app.post("/feedback", (req, res) => {
    const name = req.body.name;
    const email = req.body.email;
    const feedback = req.body.enter_your_opinions_here;
  
    // Send a POST request to the Flask app to submit the feedback
    request.post(
      {
        url: "http://127.0.0.1:5000/feedback",
        form: {
          name: name,
          email: email,
          feedback: feedback,
        },
      },
      (error, response, body) => {
        if (error) {
          console.error("Error while sending feedback:", error);
          return res.status(500).send("Error while sending feedback");
        }
        console.log("Feedback sent to Flask app:", body);
        res.redirect("feedback_success.html");
      }
    
    );
  });
app.get("/",(req,res) =>{
    res.set({
        "Allow-acces-Allow-Origin":'*'
    })
    return res.redirect('feedback.html')
}).listen(4800);

console.log("Listening on port 4800")