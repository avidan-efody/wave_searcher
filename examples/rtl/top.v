module top();
    reg clk = 0;
    reg valid1 = 0;
    reg valid2 = 0;
    reg[2:0] data;

    initial
        for(int i=0;i<20;i++) 
            #5 clk = ~clk;

    initial
        data = $urandom_range(0,7);


    initial
        begin
            int wait_time;

            wait_time = $urandom_range(1,10);

            repeat (wait_time) @(posedge clk);

            valid1 = 1'b1;

            @(posedge clk);

            valid1 = 1'b0;
        end

    initial 
        begin
            int wait_time;

            wait_time = $urandom_range(1,10);

            repeat (wait_time) @(posedge clk);

            valid2 = 1'b1;

            @(posedge clk);

            valid2 = 1'b0;
        end

  
    always @(posedge clk) 
        if ($time() > 100)
            $finish();
endmodule
