const express = require("express");
const app = express();
const util = require('util');
const execSync = require('child_process').execSync;
const exec = util.promisify(require('child_process').exec);
var bodyParser = require('body-parser');
const fileUpload = require('express-fileupload');

app.use(fileUpload());

const ACCEPTED_FILENAMES = ['setup_cni.sh', 'setup_route.sh', 'tc_mod.sh', 'custom.sh']
// const ACCEPTED_FILENAMES = ['test.sh', 'test2.sh']

// app.use(bodyParser.json());
// app.use(bodyParser.urlencoded({ extended: true }));

// // Define a middleware for our endpoint (this is required else mv method will not "commit" the file)
// app.post("/isl-reconfig", (req, res, next) => {
//     if (!req.files || Object.keys(req.files).length === 0) {
//         return res.status(400).send('No files were uploaded.');
//       }
//     // The name of the input field (i.e. "file") is used to retrieve the uploaded file(s)
//     var filelist = req.files.file;
//     const errors = [];

//     // Place filelist into an array if filelist is not already an array:
//     if (!Array.isArray(filelist)){
//         filelist = [filelist]
//         // console.log("not array")
//     }
//     // console.log(filelist)
//     for (let i = 0; i < filelist.length; i++){
        
//         // Check if filename is an accepted filename for the purposes of ISL reconfig:
//         var accepted_file = false;
//         for (let j = 0; j < ACCEPTED_FILENAMES.length; j++){
//             if (filelist[i].name == ACCEPTED_FILENAMES[j]){
//                 accepted_file = true
//             }
//         }
//         if (! accepted_file){
//             error_msg = filelist[i].name + " is not an accepted filename"
//             errors.push(error_msg);
//             continue;
//         }
        
//         // Save file in current directory with the same filename
//         // Use the mv() method to place the file somewhere on your server
//         async function async_mv(){
//             await filelist[i].mv(filelist[i].name, function(err) { // use file.name as the filename to save as in the current directory
//                 if (err){
//                     errors.push(err);
//                 }
//             });
//         }
//         async_mv();
        
//     }
//     if (errors.length != 0){
//         return res.status(500).send(errors);
//     };
//     // Assign variable to be passed on to next middleware/function
//     res.locals.filelist = filelist;  
//     next();
// });

app.post("/isl-reconfig/upload", (req, res) => {
    if (!req.files || Object.keys(req.files).length === 0) {
        return res.status(400).send('No files were uploaded.');
      }
    // The name of the input field (i.e. "file") is used to retrieve the uploaded file(s)
    var filelist = req.files.file;
    const errors = [];

    // Place filelist into an array if filelist is not already an array:
    if (!Array.isArray(filelist)){
        filelist = [filelist]
        // console.log("not array")
    }
    // console.log(filelist)
    for (let i = 0; i < filelist.length; i++){
        
        // // Check if filename is an accepted filename for the purposes of ISL reconfig:
        // var accepted_file = false;
        // for (let j = 0; j < ACCEPTED_FILENAMES.length; j++){
        //     if (filelist[i].name == ACCEPTED_FILENAMES[j]){
        //         accepted_file = true
        //     }
        // }
        // if (! accepted_file){
        //     error_msg = filelist[i].name + " is not an accepted filename"
        //     errors.push(error_msg);
        //     continue;
        // }
        
        // Save file in current directory with the same filename
        // Use the mv() method to place the file somewhere on your server
        async function async_mv(){
            await filelist[i].mv(filelist[i].name, function(err) { // use file.name as the filename to save as in the current directory
                if (err){
                    errors.push(err);
                }
            });
        }
        async_mv();
        
    }
    if (errors.length != 0){
        return res.status(500).send(errors);
    }
    else{
        res.json({
            msg: 'All file(s) uploaded and executed successfully!',
        });
    }
});

app.post("/isl-reconfig/exec", (req, res) => {
    // Execute files:
    var output_messages = [];
    const errors = [];

    if (!req.files || Object.keys(req.files).length === 0) {
        return res.status(400).send('No files were uploaded.');
      }
    // The name of the input field (i.e. "file") is used to retrieve the uploaded file(s)
    var filelist = req.files.file;

    // Place filelist into an array if filelist is not already an array:
    if (!Array.isArray(filelist)){
        filelist = [filelist]
        // console.log("not array")
    }
    for (let i = 0; i < filelist.length; i++){

        // // Check if filename is an accepted filename for the purposes of ISL reconfig:
        // var accepted_file = false;
        // for (let j = 0; j < ACCEPTED_FILENAMES.length; j++){
        //     if (filelist[i].name == ACCEPTED_FILENAMES[j]){
        //         accepted_file = true
        //     }
        // }
        // if (! accepted_file){
        //     error_msg = filelist[i].name + " is not an accepted filename"
        //     errors.push(error_msg);
        //     continue;
        // }

        var command = "sh " + filelist[i].name;
        // console.log(command)
        // const output = execSync(command, { encoding: 'utf-8' });  // the default is 'buffer'

        // async function async_exec() {
        //     const { stdout, stderr } = await exec(command);
        //     console.log('stdout:', stdout);
        //     console.error('stderr:', stderr);
        //     output_messages.push(stdout);
        //     output_messages.push(stderr);
        // }
        // async_exec();

        var myscript = exec(command, function(error, stdout, stderr){
            console.log('stdout: ' + stdout);
            console.log('stderr: ' + stderr);
            if (error !== null) {
                console.log('exec error: ' + error);
            }
            output_messages.push(stdout)
        });
    }

    if (errors.length != 0){
        return res.status(500).send(errors);
    }
    else{
        res.json({
            msg: 'All file(s) uploaded and executed successfully!',
            output_messages: output_messages
            });
    }
    // res.send('All file(s) uploaded and executed successfully!');
});

app.listen(81, () => {
    console.log("Server running on port 81");
});