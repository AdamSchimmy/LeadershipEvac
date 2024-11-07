# LeadershipEvac
 
This project is used to test the effects of leaders in evacuation scenarios. It will test whether having leaders has an impact on overall evacuation time.
    
The implementation is essentially follow the leader, where pedestrains will move towards one of many exits and leaders will also move to their own designated exit. As leaders move towards their exit, as they pass by pedestrains, they essentially "pick them up" and begin leading them to a different exit.
    
The main objective is to see if this implementation of following the leader reduces overall evacuation time and reduces congestion by splitting the pedestrians and pulling them to different exits. 