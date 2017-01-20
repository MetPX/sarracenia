#!/bin/bash

return_code=0

bash ./test_sr_sender.sh

if [ $? -eq 1 ]; then
	return_code=1
fi

bash ./test_sr_subscribe.sh 

if [ $? -eq 1 ]; then
	return_code=1
fi

exit $return_code
