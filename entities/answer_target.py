import math
import random
from dataclasses import dataclass, field
import pygame
import settings as s



@dataclass
class AnswerTarget:

    fallacy_id: str
    name: str
    bounds: tuple
    width: int
    height: int
    position: pygame.Vector2
    velocity: pygame.Vector2
    speed: float
    rng: random.Random
    heading: float
    steering: float = 0.0
    steering_target: float = 0.0
    change_remaining: float = 0.0
    accumulator: float = 0.0
    turn_rate: float = 0.0
    desired_turn: float = 0.0
    plan_remaining: float = 0.0
    feedback: str = ''
    bounds_corrections: int = 0
    previous_position: pygame.Vector2 = None
    avoidance_axes: dict = field(default_factory=dict)
    slow_time: float = 0.0
    escape_heading: float = None

    def __post_init__(self):
        """Seed the interpolation history from the hidden initial position.

        Operation:
            Copy the initial position into interpolation history.
        Input:
            The hidden initial position vector.
        Output:
            Sets previous_position to an independent copy; returns None.
        """
        self.previous_position = self.position.copy()

    @property
    def draw_position(self):
        # Operation: Interpolate between fixed-step states; at high-refresh frame rates
        #     a render frame may occur between physics ticks. Never extrapolate.
        # Input: Previous/current vectors and accumulator seconds.
        # Output: Interpolated, subpixel-quantized origin shared by drawing and clicks.
        """Return the quantized interpolated position used by both drawing and clicks.

        Operation:
            Interpolate fixed-step positions and quantize fractional coverage.
        Input:
            Previous/current positions, accumulator seconds, and subpixel settings.
        Output:
            Returns a scene-pixel Vector2 used by drawing and hit testing.
        """
        alpha=max(0.0,min(1.0,self.accumulator/s.MOTION_STEP))
        point=self.previous_position.lerp(self.position,alpha)
        scale=s.TARGET_SUBPIXEL_SCALE
        return pygame.Vector2(round(point.x*scale)/scale,round(point.y*scale)/scale)

    @property
    def x(self):
        """Return the simulation x coordinate in scene pixels.

        Operation:
            Read the simulated horizontal coordinate.
        Input:
            Current floating-point position.
        Output:
            Returns x in scene pixels without changing state.
        """
        return self.position.x

    @property
    def rect(self):
        """Return an integer approximation of the displayed label rectangle.

        Operation:
            Round the displayed origin for integer rectangle consumers.
        Input:
            Interpolated draw_position and full label dimensions.
        Output:
            Returns a pygame.Rect; contains() remains the exact fractional hit test.
        """
        point=self.draw_position
        return pygame.Rect(round(point.x), round(point.y), self.width, self.height)

    @property
    def limits(self):
        """Return padded left/top/right/bottom limits for the label origin.

        Operation:
            Inset the shared board boundary by padding and label size.
        Input:
            bounds: scene-pixel x/y/width/height; label size; TARGET_PADDING.
        Output:
            Returns left/top/right/bottom limits for the label origin.
        """
        x,y,w,h = self.bounds
        p = s.TARGET_PADDING
        return x+p, y+p, x+w-p-self.width, y+h-p-self.height

    def update(self, dt):
        """Advance this isolated target by dt seconds; shared play uses update_targets.

        Operation:
            Delegate isolated motion to the shared fixed-step updater.
        Input:
            dt: elapsed seconds; this target state.
        Output:
            Mutates this target via update_targets; returns None.
        """
        update_targets([self], dt)

    def contains(self, point):
        """Return whether a scene-pixel point lies in the displayed half-open hitbox.

        Operation:
            Apply half-open rectangle containment at the displayed origin.
        Input:
            point: scene-pixel x/y; draw_position and label dimensions.
        Output:
            Returns bool without advancing motion.
        """
        x,y=self.draw_position
        return x<=point[0]<x+self.width and y<=point[1]<y+self.height

    def plan_turn(self, neighbors):
        """Choose a curved steering rate that anticipates walls and neighboring rectangles.

        Operation:
            Score candidate curved paths against walls and predicted neighboring
            rectangles.
        Input:
            Neighbor snapshots (x, y, vx, vy, width, height), own heading/speed, and
            steering settings.
        Output:
            Returns a target angular rate in radians/second; never changes position.
        """
        left,top,right,bottom=self.limits
        margin_x=min(s.WALL_MARGIN,(right-left)*.3)
        margin_y=min(s.WALL_MARGIN,(bottom-top)*.3)
        best_cost=float('inf')
        best_turn=self.steering
        # Operation: Predict gentle arcs, including the time needed to ease into a turn.
        #     Candidate rates are steering controls, never destination positions.
        # Input: Current heading/speed, candidate turn rates, and prediction step
        #     seconds.
        # Output: Lowest-cost angular rate; candidate paths never become target
        #     positions.
        candidates=[self.steering]+[s.MAX_TURN_RATE*i/6 for i in range(-6,7)]
        h=s.STEERING_PREDICTION_STEP
        for candidate in candidates:
            x,y=self.position
            heading=self.heading
            rate=self.turn_rate
            cost=s.WANDER_TRACKING*(candidate-self.steering)**2+s.TURN_INERTIA*(candidate-self.turn_rate)**2
            for step in range(s.STEERING_PREDICTION_STEPS):
                rate += max(-s.MAX_ANGULAR_ACCELERATION*h,min(s.MAX_ANGULAR_ACCELERATION*h,(candidate-rate)*(1-math.exp(-h/s.TURN_RESPONSE))))
                heading += rate*h
                x += math.cos(heading)*self.speed*h
                y += math.sin(heading)*self.speed*h
                distances=(x-left,right-x,y-top,bottom-y)
                for d,margin in zip(distances,(margin_x,margin_x,margin_y,margin_y)):
                    cost += s.WALL_STRENGTH*max(0,(margin-d)/max(1,margin))**4
                    if d<0:cost+=10000*(1-d)
                # Operation: Rectangle separation anticipates another label entering the
                #     readability gap, accounting for both actual label sizes.
                # Input: Predicted label rectangles, neighbor velocities, and
                #     readability gap.
                # Output: Adds future overlap penalties to the candidate steering cost.
                future_time=(step+1)*h
                if future_time<=s.SEPARATION_LOOKAHEAD:
                    for ox,oy,vx,vy,ow,oh in neighbors:
                        ox+=vx*future_time;oy+=vy*future_time
                        gap=s.TARGET_READABILITY_GAP
                        overlap_x=min(x+self.width+gap,ox+ow)-max(x-gap,ox)
                        overlap_y=min(y+self.height+gap,oy+oh)-max(y-gap,oy)
                        if overlap_x>0 and overlap_y>0:
                            cost+=s.SEPARATION_STRENGTH*min(overlap_x,overlap_y)**2
                if cost>best_cost:break
            if cost<best_cost:
                best_cost,best_turn=cost,candidate
        return best_turn

    def open_heading(self, neighbors):
        """Find a clear heading for a congested target without moving it.

        Operation:
            Score escape rays when congestion reduces cruising speed.
        Input:
            Neighbor snapshots, own position/heading/speed, and padded limits.
        Output:
            Returns a heading in radians without relocating the label.
        """
        left,top,right,bottom=self.limits
        best=(float('inf'),self.heading)
        for i in range(24):
            angle=i*math.tau/24
            dx,dy=math.cos(angle),math.sin(angle)
            cost=.05*abs((angle-self.heading+math.pi)%math.tau-math.pi)
            for time in (.3,.6,1.0,1.5):
                x,y=self.position+pygame.Vector2(dx,dy)*self.speed*time
                cost+=1000*(max(0,left-x)+max(0,x-right)+max(0,top-y)+max(0,y-bottom))
                for ox,oy,vx,vy,ow,oh in neighbors:
                    ox+=vx*time;oy+=vy*time
                    overlap_x=min(x+self.width+s.TARGET_READABILITY_GAP,ox+ow)-max(x-s.TARGET_READABILITY_GAP,ox)
                    overlap_y=min(y+self.height+s.TARGET_READABILITY_GAP,oy+oh)-max(y-s.TARGET_READABILITY_GAP,oy)
                    if overlap_x>0 and overlap_y>0:cost+=100*min(overlap_x,overlap_y)**2
            if cost<best[0]:best=(cost,angle)
        return best[1]

    def step(self, dt, neighbors):
        """Advance steering history by dt seconds and return preferred velocity.

        Operation:
            Filter random steering, plan turns, recover from congestion, and limit
            acceleration.
        Input:
            dt: substep seconds; neighbor snapshots; independent RNG and motion history.
        Output:
            Updates steering/history and returns preferred Vector2 velocity; does not
            integrate position.
        """
        self.previous_position.update(self.position)
        # Operation: Refresh independent random steering targets, then filter gradually.
        # Input: dt seconds, each label's RNG, steering clock, and response settings.
        # Output: Updated steering target/rate without assigning position or velocity.
        self.change_remaining-=dt
        if self.change_remaining<=0:
            self.change_remaining+=self.rng.uniform(*s.STEERING_CHANGE_INTERVAL)
            self.steering_target=self.rng.uniform(-s.WANDER_STRENGTH,s.WANDER_STRENGTH)
        self.steering+=(self.steering_target-self.steering)*(1-math.exp(-dt/s.STEERING_RESPONSE))
        self.plan_remaining-=dt
        if self.plan_remaining<=0:
            self.desired_turn=self.plan_turn(neighbors)
            self.plan_remaining+=s.STEERING_PLAN_INTERVAL
        # Operation: Congestion recovery changes steering only; never relocate a blocked
        #     label.
        # Input: Current speed, slow_time, neighboring rectangles, and escape heading.
        # Output: Updates recovery steering without relocating the label.
        if self.velocity.length()<self.speed*.35:
            self.slow_time+=dt
        else:
            self.slow_time=max(0,self.slow_time-dt)
        if self.slow_time>s.ESCAPE_DELAY and self.escape_heading is None:
            self.escape_heading=self.open_heading(neighbors)
        if self.escape_heading is not None:
            if self.velocity.length()>self.speed*.7:
                self.escape_heading=None
                self.slow_time=0
            else:
                difference=(self.escape_heading-self.heading+math.pi)%math.tau-math.pi
                self.desired_turn=max(-s.MAX_TURN_RATE,min(s.MAX_TURN_RATE,difference/.4))
        # Operation: Filter angular acceleration before deriving the preferred linear
        #     velocity.
        # Input: Desired/current angular rates, dt seconds, and acceleration limit.
        # Output: Updates turn_rate gradually before linear velocity calculation.
        change=(self.desired_turn-self.turn_rate)*(1-math.exp(-dt/s.TURN_RESPONSE))
        self.turn_rate+=max(-s.MAX_ANGULAR_ACCELERATION*dt,min(s.MAX_ANGULAR_ACCELERATION*dt,change))
        # Operation: Steer toward nominal cruising speed; avoidance can ease speed down.
        #     Limit acceleration as well as angular rate to keep turns comfortable.
        # Input: Heading, nominal speed, current velocity, and dt seconds.
        # Output: Returns smoothly limited preferred velocity; position is not
        #     integrated here.
        turn_limit=min(s.MAX_TURN_RATE,s.MAX_ACCELERATION/max(1,self.speed))
        self.turn_rate=max(-turn_limit,min(turn_limit,self.turn_rate))
        self.heading+=self.turn_rate*dt
        preferred=pygame.Vector2(math.cos(self.heading)*self.speed,math.sin(self.heading)*self.speed)
        change=(preferred-self.velocity)*(1-math.exp(-dt/s.VELOCITY_RESPONSE))
        if change.length()>s.MAX_ACCELERATION*dt:
            change.scale_to_length(s.MAX_ACCELERATION*dt)
        return self.velocity+change


def safe_velocities(targets, preferred, horizon):
    """Project velocities onto shared rectangle-clearance constraints.

    Operation:
        Project preferred velocities onto wall and pairwise rectangle-clearance
        constraints. Position is NEVER corrected to separate labels. Each separating
        axis limits closing velocity before contact, leaving tangential motion free. The
        slow approach bound gives steering time to curve around the other rectangle.
    Input:
        targets, preferred velocity vectors, and horizon seconds; current separation and
        solver settings.
    Output:
        Returns safe velocity vectors and updates separating-axis history. Raises
        RuntimeError if no valid separating face exists; never translates positions.
    """
    velocities=[v.copy() for v in preferred]
    constraints=[]
    gap=s.TARGET_READABILITY_GAP+2  # room for raster/interpolation rounding
    for i,a in enumerate(targets):
        ax,ay=a.position
        for j in range(i+1,len(targets)):
            b=targets[j]
            bx,by=b.position
            dx=(ax+a.width/2)-(bx+b.width/2)
            dy=(ay+a.height/2)-(by+b.height/2)
            gx=abs(dx)-(a.width+b.width)/2-gap
            gy=abs(dy)-(a.height+b.height)/2-gap
            # Operation: Choose a separating face, using actual rectangular extents.
            #     Long labels most often pass above/below, rather than detouring
            #     hundreds of pixels around each other's centers. Two pixels of reserve
            #     absorb raster rounding and solver residuals.
            # Input: Current full rectangles and readability gap plus rounding reserve.
            # Output: Candidate separating axes and raw clearance; invalid layouts raise
            #     RuntimeError.
            axes=[]
            if gx>=-2:axes.append((max(0,gx)/(a.width+b.width),0,1 if dx>=0 else -1,gx))
            if gy>=-2:axes.append((max(0,gy)/(a.height+b.height),1,1 if dy>=0 else -1,gy))
            if not axes:
                raise RuntimeError('Target rectangles lost their clearance before integration.')
            previous=a.avoidance_axes.get(b.fallacy_id)
            _,axis,sign,clearance=max(axes)
            if previous is not None:
                old=next((entry for entry in axes if entry[1]==previous),None)
                if old is not None:
                    alternatives=[entry for entry in axes if entry[1]!=previous]
                    # Operation: Switch faces only when the alternative already has room
                    #     for the current closing velocity. This hysteresis avoids a
                    #     sudden velocity change at diagonal/corner encounters.
                    # Input: Previous axis, alternative clearance, closing speed, and
                    #     horizon seconds.
                    # Output: Retains stable avoidance axis unless the alternative
                    #     already has room.
                    safe_alternative=[]
                    for entry in alternatives:
                        _,alt,alt_sign,alt_gap=entry
                        closing=max(0,-alt_sign*(a.velocity[alt]-b.velocity[alt]))
                        if alt_gap>closing*horizon+s.SEPARATION_FACE_HYSTERESIS:
                            safe_alternative.append(entry)
                    _,axis,sign,clearance=max(safe_alternative) if safe_alternative else old
            a.avoidance_axes[b.fallacy_id]=axis
            constraints.append((i,j,axis,sign,max(0,clearance)/horizon,clearance))
    # Operation: Zero velocity is always feasible for the current separated layout. Use
    #     cyclic projections to share the needed adjustment between both labels.
    # Input: Preferred velocities, pair constraints, wall limits, and solver iterations.
    # Output: Projects velocities cyclically, sharing clearance adjustments between
    #     labels.
    for _ in range(s.SEPARATION_SOLVER_ITERATIONS):
        for i,t in enumerate(targets):
            left,top,right,bottom=t.limits
            velocities[i].x=max((left-t.position.x)/horizon,min((right-t.position.x)/horizon,velocities[i].x))
            velocities[i].y=max((top-t.position.y)/horizon,min((bottom-t.position.y)/horizon,velocities[i].y))
        changed=False
        for i,j,axis,sign,allowed_closing,clearance in constraints:
            closing=-sign*(velocities[i][axis]-velocities[j][axis])
            excess=closing-allowed_closing
            if excess>1e-9:
                velocities[i][axis]+=sign*excess*.5
                velocities[j][axis]-=sign*excess*.5
                changed=True
        if not changed:break
    # Operation: A uniform velocity reduction makes any small iterative-solver residual
    #     safe without translating positions or changing direction. Normally 1.0.
    # Input: Residual closing velocities, true clearance, and fixed-step seconds.
    # Output: Scales velocities uniformly when needed; positions/directions are not
    #     corrected.
    factor=1.0
    for i,t in enumerate(targets):
        left,top,right,bottom=t.limits
        for axis,lo,hi in ((0,left,right),(1,top,bottom)):
            v=velocities[i][axis]
            if v>0:factor=min(factor,max(0,(hi-t.position[axis])/(v*s.MOTION_STEP)))
            elif v<0:factor=min(factor,max(0,(t.position[axis]-lo)/(-v*s.MOTION_STEP)))
    for i,j,axis,sign,allowed_closing,clearance in constraints:
        closing=-sign*(velocities[i][axis]-velocities[j][axis])
        allowed_step=max(0,clearance+2)/s.MOTION_STEP
        if closing>allowed_step and closing>0:factor=min(factor,allowed_step/closing)
    return [v*factor for v in velocities]


def update_targets(targets, dt):
    """Integrate shared targets with bounded, fixed-duration simulation substeps.

    Operation:
        Consume bounded fixed substeps using shared snapshots, projection, and
        integration.
    Input:
        targets: mutable labels; dt: seconds; speed multiplier and catch-up settings.
    Output:
        Updates positions, velocities, and interpolation/steering history in place;
        returns None. Nonpositive time/speed leaves state unchanged.
    """
    if not targets or dt<=0 or s.LABEL_SPEED_MULTIPLIER<=0:
        return
    # Operation: Bound catch-up work after a stalled frame; don't replay seconds of
    #     motion in one visible frame. Normal 30/60/144 FPS all consume identical steps.
    # Input: Frame dt, speed multiplier, and maximum catch-up seconds.
    # Output: Adds bounded elapsed time to target accumulators instead of replaying a
    #     long stall.
    elapsed = min(dt,s.MOTION_MAX_CATCHUP)*s.LABEL_SPEED_MULTIPLIER
    for t in targets:
        t.accumulator += elapsed
    while targets[0].accumulator+1e-10 >= s.MOTION_STEP:
        # Operation: Plan from one shared snapshot, then project velocities and
        #     integrate together.
        # Input: All current target states and one fixed substep.
        # Output: Plans from a common snapshot, projects velocities, then integrates
        #     positions.
        snapshots=[(t.position.x,t.position.y,t.velocity.x,t.velocity.y,t.width,t.height) for t in targets]
        preferred=[t.step(s.MOTION_STEP,snapshots[:i]+snapshots[i+1:]) for i,t in enumerate(targets)]
        velocities=safe_velocities(targets,preferred,s.SEPARATION_HORIZON)
        for t,velocity in zip(targets,velocities):
            t.velocity.update(velocity)
            t.position+=t.velocity*s.MOTION_STEP
            t.accumulator=max(0,t.accumulator-s.MOTION_STEP)


def make_targets(choices, fallacies, rng):
    """Create separated, hidden labels with independent random steering state.

    Operation:
        Pack separated hidden labels, then initialize independent steering generators.
    Input:
        choices: 2–8 fallacy IDs; fallacies: name mapping; rng: session generator.
    Output:
        Returns targets sharing LABEL_REGION. Raises ValueError for unsupported counts
        or failed packing; randomness is consumed only during initialization.
    """
    count=len(choices)
    if not 2<=count<=s.MAX_CHOICES:
        raise ValueError('Answer count must be between 2 and 8.')
    bounds=s.LABEL_REGION
    bx,by,bw,bh=bounds
    width,height,factor=(s.LABEL_WIDTH,44,1.0) if count<=3 else (s.DENSE_LABEL_WIDTH,34,s.DENSE_SPEED_FACTOR)
    p=s.TARGET_PADDING
    # Operation: Random sequential packing is used ONLY before the hidden targets
    #     appear. No spawn grid becomes a movement zone: all targets retain the same
    #     bounds.
    # Input: Shared board interior, label sizes, spawn gap, and session RNG.
    # Output: Separated hidden start positions; failed packing raises ValueError.
    positions=[]
    for attempt in range(100):
        positions=[]
        for _ in choices:
            for trial in range(500):
                point=pygame.Vector2(rng.uniform(bx+p,bx+bw-p-width),rng.uniform(by+p,by+bh-p-height))
                if all(not (abs(point.x-other.x)<width+s.TARGET_SPAWN_GAP and
                            abs(point.y-other.y)<height+s.TARGET_SPAWN_GAP) for other in positions):
                    positions.append(point)
                    break
            else:break
        if len(positions)==count:break
    else:raise ValueError('Answer box cannot fit the configured labels and spawn gap.')
    # Operation: All randomness below initializes hidden state before the round is
    #     visible.
    # Input: Packed positions, fallacy names, and session RNG.
    # Output: Independent hidden steering states; every target retains the full shared
    #     bounds.
    targets=[]
    for id_,position in zip(choices,positions):
        local=random.Random(rng.getrandbits(64))
        heading=local.uniform(-math.pi,math.pi)
        speed=local.uniform(*s.TARGET_SPEED)*factor
        velocity=pygame.Vector2(math.cos(heading),math.sin(heading))*speed
        margin=s.WALL_MARGIN+speed*.6
        if (position.x<bx+p+margin and velocity.x<0) or (position.x>bx+bw-p-width-margin and velocity.x>0):velocity.x*=-1
        if (position.y<by+p+margin and velocity.y<0) or (position.y>by+bh-p-height-margin and velocity.y>0):velocity.y*=-1
        heading=math.atan2(velocity.y,velocity.x)
        targets.append(AnswerTarget(id_,fallacies[id_]['name'],bounds,width,height,position,velocity,speed,local,heading,
                                    steering_target=local.uniform(-s.WANDER_STRENGTH,s.WANDER_STRENGTH),
                                    change_remaining=local.uniform(*s.STEERING_CHANGE_INTERVAL),
                                    plan_remaining=local.uniform(0,s.STEERING_PLAN_INTERVAL)))
    initial=safe_velocities(targets,[t.velocity for t in targets],s.SEPARATION_HORIZON)
    for target,velocity in zip(targets,initial):
        target.velocity.update(velocity)
    return targets