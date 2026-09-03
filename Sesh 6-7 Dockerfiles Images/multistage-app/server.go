package main

import (
	"fmt"
	"log"
	"net/http"
)

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintln(w, "Hello World from Docker multi-stage build")
}

func main() {
	http.HandleFunc("/", handler)
	log.Println("Server listening on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
